"""FastAPI application factory with middleware, exception handlers, and router registration."""

import asyncio
import secrets
import time as _time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import (
    HTTPException as FastAPIHTTPException,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    ExternalAPIError,
    KaleidoscopeError,
    PaperNotFoundError,
    RateLimitError,
)

logger = structlog.get_logger(__name__)


API_KEY_HEADER_NAMES = ("X-API-Key", "X-Kaleidoscope-API-Key")
API_KEY_PROTECTED_PREFIXES = ("/api/v1",)
API_KEY_PROTECTED_PATHS = ("/api/openapi.json", "/health", "/health/services")


def _api_key_error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
        headers={"WWW-Authenticate": 'ApiKey realm="Kaleidoscope"'},
    )


def _is_api_key_protected_request(request: Request) -> bool:
    if request.method == "OPTIONS":
        return False
    path = request.url.path.rstrip("/") or "/"
    if path in API_KEY_PROTECTED_PATHS:
        return True
    return any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in API_KEY_PROTECTED_PREFIXES
    )


def _extract_api_key_token(request: Request) -> str | None:
    for header_name in API_KEY_HEADER_NAMES:
        value = request.headers.get(header_name)
        if value and value.strip():
            return value.strip()

    auth_header = request.headers.get("Authorization", "")
    scheme, _, credentials = auth_header.partition(" ")
    if scheme.lower() == "bearer" and credentials.strip():
        return credentials.strip()

    query_key = request.query_params.get("api_key")
    if query_key and query_key.strip():
        return query_key.strip()
    return None


def _matches_configured_api_key(token: str) -> bool:
    return any(
        secrets.compare_digest(token, configured_key)
        for configured_key in settings.external_api_keys
        if configured_key
    )


async def _authenticate_api_key_request(request: Request) -> JSONResponse | None:
    """Require API keys for externally exposed API paths."""
    if (
        not settings.external_api_key_required
        or not _is_api_key_protected_request(request)
    ):
        return None

    token = _extract_api_key_token(request)
    if token is None:
        return _api_key_error(
            401,
            "API_KEY_REQUIRED",
            "API key required. Send X-API-Key or Authorization: Bearer.",
        )

    if _matches_configured_api_key(token):
        from app.models.collection import DEFAULT_USER_ID

        request.state.user_id = DEFAULT_USER_ID
        request.state.api_key_id = "configured"
        request.state.api_key_scopes = ["*"]
        return None

    if not token.startswith("ks_live_"):
        return _api_key_error(
            401,
            "INVALID_API_KEY",
            "Invalid, revoked, or expired API key.",
        )

    from sqlalchemy import select

    from app.dependencies import async_session_factory
    from app.models.api_key import APIKey
    from app.services.api_key_service import APIKeyService

    now = datetime.now(tz=UTC)
    key_hash = APIKeyService.hash_key(token)
    async with async_session_factory() as session:
        result = await session.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.revoked_at.is_(None),
            )
        )
        api_key = result.scalar_one_or_none()
        expires_at = api_key.expires_at if api_key is not None else None
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if api_key is None or (expires_at is not None and expires_at <= now):
            return _api_key_error(
                401,
                "INVALID_API_KEY",
                "Invalid, revoked, or expired API key.",
            )

        api_key.last_used_at = now
        await session.commit()
        request.state.user_id = str(api_key.user_id)
        request.state.api_key_id = str(api_key.id)
        request.state.api_key_scopes = list(api_key.scopes or [])

    return None


async def _background_enrich_authors() -> None:
    """
    Enrich all authors that don't yet have a Semantic Scholar ID.
    Runs as a fire-and-forget background task on startup.
    Processes in small batches to respect S2 free-tier rate limits.
    """
    from sqlalchemy import select

    from app.dependencies import async_session_factory
    from app.models.author import Author
    from app.services.enrichment.author_enrichment import AuthorEnrichmentService

    try:
        # Delay startup enrichment so foreground requests always get first pick of S2 quota
        await asyncio.sleep(300)  # 5 minutes

        async with async_session_factory() as session:
            result = await session.execute(
                select(Author.id, Author.display_name)
                .where(
                    Author.deleted_at.is_(None),
                    Author.semantic_scholar_id.is_(None),
                )
                .order_by(Author.display_name)
            )
            rows = result.all()

        if not rows:
            logger.info(
                "author_enrich_startup_skip", reason="all authors already enriched"
            )
            return

        logger.info("author_enrich_startup_begin", count=len(rows))
        ok = no_match = errors = 0

        for i in range(0, len(rows), 5):
            batch = rows[i : i + 5]

            async def _one(author_id: str, name: str) -> None:
                nonlocal ok, no_match, errors
                try:
                    async with async_session_factory() as db:
                        svc = AuthorEnrichmentService(db, background=True)
                        res = await svc.enrich(author_id)
                        await svc.close()
                    status = res.get("status", "error")
                    if status == "ok":
                        ok += 1
                        logger.info(
                            "author_enriched_bg",
                            name=name,
                            s2_id=res.get("s2_id"),
                            reason=res.get("match_reason"),
                        )
                    elif status == "no_match":
                        no_match += 1
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    logger.warning(
                        "author_enrich_bg_error", name=name, error=str(e)[:120]
                    )

            await asyncio.gather(
                *[_one(str(r.id), r.display_name) for r in batch],
                return_exceptions=True,
            )
            if i + 5 < len(rows):
                await asyncio.sleep(4)  # stay under 100 req / 5 min

        logger.info(
            "author_enrich_startup_done", ok=ok, no_match=no_match, errors=errors
        )

    except Exception as e:
        logger.warning("author_enrich_startup_failed", error=str(e))


async def _background_label_papers() -> None:
    """
    Label all papers that don't yet have taxonomy labels.
    Runs as a fire-and-forget background task on startup.
    Uses concurrency=50 (LLM API supports it) with asyncio.Semaphore.
    """
    from sqlalchemy import select

    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from app.services.analysis.labeling_service import LabelingService

    try:
        # Start after author enrichment is well underway
        await asyncio.sleep(600)  # 10 minutes

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper.id)
                .where(
                    Paper.deleted_at.is_(None),
                    Paper.paper_labels.is_(None),
                    Paper.title != "",
                    Paper.full_text_markdown.is_not(None),
                )
                .order_by(Paper.created_at.desc())
            )
            paper_ids = [row[0] for row in result.all()]

        if not paper_ids:
            logger.info("label_startup_skip", reason="all papers already labeled")
            return

        logger.info("label_startup_begin", count=len(paper_ids))
        done = errors = 0
        # Concurrency limited to 10 to stay within the DB connection pool (size=20+overflow=10)
        # The LLM API supports higher parallelism but each task holds a DB session during the call
        sem = asyncio.Semaphore(10)

        async def _one(paper_id) -> None:
            nonlocal done, errors
            async with sem:
                try:
                    async with async_session_factory() as db:
                        r = await db.execute(select(Paper).where(Paper.id == paper_id))
                        paper = r.scalar_one_or_none()
                        if paper is None or paper.paper_labels is not None:
                            return
                        svc = LabelingService(db)
                        await svc.label_paper(paper)
                        await db.commit()
                        await svc.close()
                    done += 1
                except Exception as e:
                    errors += 1
                    logger.warning(
                        "label_bg_error",
                        paper_id=str(paper_id),
                        error=str(e)[:120],
                    )

        await asyncio.gather(*[_one(pid) for pid in paper_ids], return_exceptions=True)
        logger.info("label_startup_done", done=done, errors=errors)

    except Exception as e:
        logger.warning("label_startup_failed", error=str(e))


async def _background_analyse_papers() -> None:
    """
    Deep-analyse all papers that don't yet have deep_analysis.
    Runs as a fire-and-forget background task on startup.
    Concurrency=3: analysis holds a DB session + makes a long LLM call (~90s each),
    so keep well below the pool limit (20+10=30).
    Starts after labeling is well underway (15 minutes delay).
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.dependencies import async_session_factory
    from app.models.author import PaperAuthor
    from app.models.paper import Paper
    from app.services.analysis.paper_analyst import PaperAnalystService

    try:
        await asyncio.sleep(900)  # 15 minutes — let labeling run first

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper.id)
                .where(
                    Paper.deleted_at.is_(None),
                    Paper.deep_analysis.is_(None),
                    Paper.title != "",
                    Paper.full_text_markdown.is_not(None),
                )
                .order_by(Paper.created_at.desc())
            )
            paper_ids = [row[0] for row in result.all()]

        if not paper_ids:
            logger.info("analysis_startup_skip", reason="all papers already analysed")
            return

        logger.info("analysis_startup_begin", count=len(paper_ids))
        done = errors = 0
        sem = asyncio.Semaphore(3)  # long LLM calls: keep DB sessions low

        async def _one(paper_id) -> None:
            nonlocal done, errors
            async with sem:
                try:
                    async with async_session_factory() as db:
                        r = await db.execute(
                            select(Paper)
                            .where(Paper.id == paper_id)
                            .options(
                                selectinload(Paper.authors).selectinload(
                                    PaperAuthor.author
                                )
                            )
                        )
                        paper = r.scalar_one_or_none()
                        if paper is None or paper.deep_analysis is not None:
                            return
                        svc = PaperAnalystService(db)
                        await svc.analyse_and_persist(paper, db)
                        await db.commit()
                        await svc.close()
                    done += 1
                except Exception as e:
                    errors += 1
                    logger.warning(
                        "analysis_bg_error",
                        paper_id=str(paper_id),
                        error=str(e)[:120],
                    )

        await asyncio.gather(*[_one(pid) for pid in paper_ids], return_exceptions=True)
        logger.info("analysis_startup_done", done=done, errors=errors)

    except Exception as e:
        logger.warning("analysis_startup_failed", error=str(e))


async def _background_overview_images() -> None:
    """
    Generate 一图速览 posters for papers that have deep_analysis but no overview_image.
    Runs as a fire-and-forget background task on startup.
    Concurrency=1: each job runs a long LLM call + image API call + OSS upload (~3-5 min).
    Starts after analysis is well underway (20 minutes delay).
    """
    from datetime import datetime

    from sqlalchemy import select

    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from app.services.analysis.overview_image_service import OverviewImageService
    from app.services.analysis.paper_analyst import deep_analysis_is_valid

    try:
        await asyncio.sleep(1200)  # 20 minutes — let analysis sweep run first

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper.id, Paper.title, Paper.deep_analysis, Paper.overview_image)
                .where(
                    Paper.deleted_at.is_(None),
                    Paper.deep_analysis.is_not(None),
                )
                .order_by(Paper.created_at.desc())
            )
            rows = result.all()

        # Only process papers where deep_analysis succeeded and overview_image is missing/failed
        candidates = [
            r
            for r in rows
            if deep_analysis_is_valid(r.deep_analysis)
            and r.title.strip()
            and (r.overview_image or {}).get("status") not in ("ok", "generating")
        ]

        if not candidates:
            logger.info(
                "overview_image_startup_skip",
                reason="all eligible papers already have overview images",
            )
            return

        logger.info("overview_image_startup_begin", count=len(candidates))
        done = errors = 0
        sem = asyncio.Semaphore(
            1
        )  # image generation is expensive: LLM + image API + OSS

        async def _one(paper_id, paper_title: str, deep_analysis: dict) -> None:
            nonlocal done, errors
            async with sem:
                try:
                    analysis_text = deep_analysis.get("analysis", "")
                    if not analysis_text:
                        return

                    # Mark as generating
                    async with async_session_factory() as db:
                        r = await db.execute(select(Paper).where(Paper.id == paper_id))
                        paper = r.scalar_one_or_none()
                        if paper is None:
                            return
                        # Re-check: another path may have generated it already
                        if (paper.overview_image or {}).get("status") in (
                            "ok",
                            "generating",
                        ):
                            return
                        paper.overview_image = {"status": "generating"}
                        paper.overview_image_at = datetime.now(UTC)
                        await db.commit()

                    # Generate image
                    svc = OverviewImageService()
                    try:
                        url = await svc.generate(paper_title, analysis_text)
                        image_data = {
                            "status": "ok",
                            "url": url,
                            "generated_at": datetime.now(UTC).isoformat(),
                        }
                        done += 1
                        logger.info(
                            "overview_image_bg_done",
                            paper_id=str(paper_id),
                            title=paper_title[:60],
                        )
                    except Exception as e:
                        image_data = {"status": "error", "error": str(e)[:300]}
                        errors += 1
                        logger.warning(
                            "overview_image_bg_error",
                            paper_id=str(paper_id),
                            error=str(e)[:120],
                        )
                    finally:
                        await svc.close()

                    # Persist result
                    async with async_session_factory() as db:
                        r = await db.execute(select(Paper).where(Paper.id == paper_id))
                        paper = r.scalar_one_or_none()
                        if paper is not None:
                            paper.overview_image = image_data
                            paper.overview_image_at = datetime.now(UTC)
                            await db.commit()

                except Exception as e:
                    errors += 1
                    logger.warning(
                        "overview_image_bg_outer_error",
                        paper_id=str(paper_id),
                        error=str(e)[:120],
                    )

        await asyncio.gather(
            *[_one(r.id, r.title, r.deep_analysis) for r in candidates],
            return_exceptions=True,
        )
        logger.info("overview_image_startup_done", done=done, errors=errors)

    except Exception as e:
        logger.warning("overview_image_startup_failed", error=str(e))


async def _background_translate_analyses() -> None:
    """
    Translate deep_analysis text to Chinese for papers that have deep_analysis but
    no deep_analysis_zh.  RPM=20 → one request every 3 seconds, sequential.
    Starts 25 minutes after startup (after analysis + image sweeps).
    """
    from datetime import datetime

    from sqlalchemy import select

    from app.clients.translate_client import TranslateClient
    from app.dependencies import async_session_factory
    from app.models.paper import Paper

    _system_prompt = (
        "你是一个翻译助手。使用专业简洁的术语，把英文翻译为中文。"
        "无任何其他输出。严格保持输出格式与输入的内容格式一致"
    )

    try:
        await asyncio.sleep(1500)  # 25 minutes

        async with async_session_factory() as session:
            result = await session.execute(
                select(Paper.id, Paper.deep_analysis, Paper.deep_analysis_zh)
                .where(
                    Paper.deleted_at.is_(None),
                    Paper.deep_analysis.is_not(None),
                )
                .order_by(Paper.created_at.desc())
            )
            rows = result.all()

        candidates = [
            r
            for r in rows
            if (r.deep_analysis or {}).get("status") == "ok"
            and (r.deep_analysis_zh or {}).get("status") not in ("ok", "translating")
        ]

        if not candidates:
            logger.info(
                "translate_zh_startup_skip",
                reason="all eligible papers already have Chinese translation",
            )
            return

        logger.info("translate_zh_startup_begin", count=len(candidates))
        done = errors = 0

        for r in candidates:
            paper_id = r.id
            analysis_text = (r.deep_analysis or {}).get("analysis", "")
            if not analysis_text:
                continue

            # Mark as translating
            async with async_session_factory() as db:
                p = (
                    await db.execute(select(Paper).where(Paper.id == paper_id))
                ).scalar_one_or_none()
                if p is None:
                    continue
                if (p.deep_analysis_zh or {}).get("status") in ("ok", "translating"):
                    continue
                p.deep_analysis_zh = {"status": "translating"}
                p.deep_analysis_zh_at = datetime.now(UTC)
                await db.commit()

            try:
                async with TranslateClient(system_prompt=_system_prompt) as client:
                    translated = await client.translate(
                        analysis_text, system_prompt=_system_prompt
                    )

                if translated:
                    zh_data = {
                        "status": "ok",
                        "analysis": translated,
                        "translated_at": datetime.now(UTC).isoformat(),
                    }
                    done += 1
                else:
                    zh_data = {"status": "error", "error": "empty result"}
                    errors += 1
            except Exception as e:
                zh_data = {"status": "error", "error": str(e)[:300]}
                errors += 1
                logger.warning(
                    "translate_zh_bg_error", paper_id=str(paper_id), error=str(e)[:120]
                )

            async with async_session_factory() as db:
                p = (
                    await db.execute(select(Paper).where(Paper.id == paper_id))
                ).scalar_one_or_none()
                if p is not None:
                    p.deep_analysis_zh = zh_data
                    p.deep_analysis_zh_at = datetime.now(UTC)
                    await db.commit()

            # RPM=20 → 3 seconds between requests
            await asyncio.sleep(3)

        logger.info("translate_zh_startup_done", done=done, errors=errors)

    except Exception as e:
        logger.warning("translate_zh_startup_failed", error=str(e))


async def _background_fetch_links() -> None:
    """
    Fetch AI-powered paper links for papers that don't have them yet.
    Concurrency=2.  Starts 10 minutes after startup.
    """
    from datetime import datetime

    from sqlalchemy import select

    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from app.services.analysis.links_service import LinksService

    try:
        await asyncio.sleep(600)  # 10 minutes

        async with async_session_factory() as session:
            result = await session.execute(
                select(
                    Paper.id, Paper.title, Paper.arxiv_id, Paper.doi, Paper.paper_links
                )
                .where(Paper.deleted_at.is_(None), Paper.title != "")
                .order_by(Paper.created_at.desc())
            )
            rows = result.all()

        candidates = [
            r
            for r in rows
            if (r.paper_links or {}).get("status") not in ("ok", "fetching")
            and r.title.strip()
        ]

        if not candidates:
            logger.info(
                "fetch_links_startup_skip", reason="all papers already have links"
            )
            return

        logger.info("fetch_links_startup_begin", count=len(candidates))
        done = errors = 0
        sem = asyncio.Semaphore(2)

        async def _one(
            paper_id, title: str, arxiv_id: str | None, doi: str | None
        ) -> None:
            nonlocal done, errors
            async with sem:
                try:
                    # Mark as fetching (re-check first)
                    async with async_session_factory() as db:
                        p = (
                            await db.execute(select(Paper).where(Paper.id == paper_id))
                        ).scalar_one_or_none()
                        if p is None:
                            return
                        if (p.paper_links or {}).get("status") in ("ok", "fetching"):
                            return
                        p.paper_links = {"status": "fetching"}
                        p.paper_links_at = datetime.now(UTC)
                        await db.commit()

                    async with LinksService() as svc:
                        links = await svc.fetch_links(title, arxiv_id=arxiv_id, doi=doi)

                    links_data = {
                        "status": "ok",
                        "fetched_at": datetime.now(UTC).isoformat(),
                        **links,
                    }
                    done += 1
                    logger.info(
                        "fetch_links_bg_done", paper_id=str(paper_id), title=title[:60]
                    )
                except Exception as e:
                    links_data = {"status": "error", "error": str(e)[:300]}
                    errors += 1
                    logger.warning(
                        "fetch_links_bg_error",
                        paper_id=str(paper_id),
                        error=str(e)[:120],
                    )

                try:
                    async with async_session_factory() as db:
                        p = (
                            await db.execute(select(Paper).where(Paper.id == paper_id))
                        ).scalar_one_or_none()
                        if p is not None:
                            p.paper_links = links_data
                            p.paper_links_at = datetime.now(UTC)
                            await db.commit()
                except Exception:
                    pass

        await asyncio.gather(
            *[_one(r.id, r.title, r.arxiv_id, r.doi) for r in candidates],
            return_exceptions=True,
        )
        logger.info("fetch_links_startup_done", done=done, errors=errors)

    except Exception as e:
        logger.warning("fetch_links_startup_failed", error=str(e))


async def _background_embed_papers() -> None:
    """
    Scan all papers and embed any that are missing a completed PaperEmbeddingJob.
    Runs immediately on startup with no delay — embedding is fast (seconds per paper)
    and does not block any foreground requests.
    Concurrency=5: each paper holds a DB session + one LLM embed call.
    """
    from sqlalchemy import exists, not_, select

    from app.dependencies import async_session_factory
    from app.models.paper import Paper
    from app.models.paper_qa import PaperEmbeddingJob
    from app.tasks.embedding_tasks import embed_paper_async

    try:
        async with async_session_factory() as session:
            # Papers with no job at all
            no_job_ids = (
                (
                    await session.execute(
                        select(Paper.id).where(
                            Paper.deleted_at.is_(None),
                            not_(
                                exists(
                                    select(PaperEmbeddingJob.id).where(
                                        PaperEmbeddingJob.paper_id == Paper.id
                                    )
                                )
                            ),
                        )
                    )
                )
                .scalars()
                .all()
            )

            # Papers whose last job failed
            failed_ids = (
                (
                    await session.execute(
                        select(Paper.id)
                        .join(PaperEmbeddingJob, PaperEmbeddingJob.paper_id == Paper.id)
                        .where(
                            Paper.deleted_at.is_(None),
                            PaperEmbeddingJob.status == "failed",
                        )
                    )
                )
                .scalars()
                .all()
            )

        all_ids = list(
            dict.fromkeys([str(i) for i in no_job_ids] + [str(i) for i in failed_ids])
        )

        if not all_ids:
            logger.info("embed_startup_skip", reason="all papers already embedded")
            return

        logger.info("embed_startup_begin", count=len(all_ids))
        done = errors = skipped = 0
        sem = asyncio.Semaphore(5)

        async def _one(paper_id: str) -> None:
            nonlocal done, errors, skipped
            async with sem:
                try:
                    result = await embed_paper_async(paper_id, priority=0)
                    if result.get("skipped"):
                        skipped += 1
                    elif result.get("status") == "completed":
                        done += 1
                    else:
                        errors += 1
                        logger.warning(
                            "embed_startup_paper_failed",
                            paper_id=paper_id,
                            error=result.get("error"),
                        )
                except Exception as e:
                    errors += 1
                    logger.warning(
                        "embed_startup_error", paper_id=paper_id, error=str(e)[:120]
                    )

        await asyncio.gather(*[_one(pid) for pid in all_ids], return_exceptions=True)
        logger.info("embed_startup_done", done=done, errors=errors, skipped=skipped)

    except Exception as e:
        logger.warning("embed_startup_failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────
    asyncio.create_task(_background_embed_papers())
    asyncio.create_task(_background_enrich_authors())
    asyncio.create_task(_background_label_papers())
    asyncio.create_task(_background_analyse_papers())
    asyncio.create_task(_background_overview_images())
    asyncio.create_task(_background_translate_analyses())
    asyncio.create_task(_background_fetch_links())
    yield
    # ── Shutdown ─────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Kaleidoscope API",
        lifespan=lifespan,
        description=(
            "Academic Paper Intelligence Platform — "
            "Ingest, search, and analyze scholarly papers with AI."
        ),
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/api/openapi.json",
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, "allowed_origins", ["*"]),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = _time.monotonic()
        auth_error = await _authenticate_api_key_request(request)
        response = auth_error if auth_error is not None else await call_next(request)
        response.headers.setdefault("X-RateLimit-Policy", "deployment-configured")
        scopes = getattr(request.state, "api_key_scopes", None)
        if scopes is not None:
            response.headers.setdefault("X-API-Key-Scopes", " ".join(scopes))
        elapsed = _time.monotonic() - start
        elapsed_ms = elapsed * 1000
        if elapsed > 5.0:
            route_path = request.scope.get("path", "")
            if "reparse" in route_path or "graph" in route_path:
                logger.warning(
                    "slow_operation_detected",
                    path=route_path,
                    elapsed_s=round(elapsed, 2),
                    method=request.method,
                )
        if not request.url.path.startswith("/health"):
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=f"{elapsed_ms:.1f}",
            )
        return response

    # --- Exception Handlers ---

    @app.exception_handler(PaperNotFoundError)
    async def paper_not_found_handler(request: Request, exc: PaperNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "code": "PAPER_NOT_FOUND",
                "message": str(exc),
            },
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        return JSONResponse(
            status_code=429,
            content={
                "code": "RATE_LIMITED",
                "message": str(exc),
                "retry_after": exc.retry_after,
            },
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(ExternalAPIError)
    async def external_api_handler(request: Request, exc: ExternalAPIError):
        return JSONResponse(
            status_code=502,
            content={
                "code": "EXTERNAL_API_ERROR",
                "message": str(exc),
                "service": exc.service,
            },
        )

    @app.exception_handler(KaleidoscopeError)
    async def kaleidoscope_error_handler(request: Request, exc: KaleidoscopeError):
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
        if isinstance(exc.detail, dict):
            detail = exc.detail
            content = {
                "code": detail.get("code", f"HTTP_{exc.status_code}"),
                "message": detail.get("message")
                or detail.get("detail")
                or "An error occurred.",
            }
            for key, value in detail.items():
                if key not in {"code", "message"}:
                    content[key] = value
        else:
            content = {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail) if exc.detail else "An error occurred.",
            }
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": [
                    {"field": ".".join(str(loc) for loc in e["loc"]), "msg": e["msg"]}
                    for e in errors
                ],
            },
        )

    # --- Register Routers ---
    from app.api.v1 import ragflow as ragflow_router
    from app.api.v1.agent import router as agent_router
    from app.api.v1.agent_services import router as agent_services_router
    from app.api.v1.alerts import router as alerts_router
    from app.api.v1.analysis import router as analysis_router
    from app.api.v1.answers import router as answers_router
    from app.api.v1.api_keys import router as api_keys_router
    from app.api.v1.auth import router as auth_router
    from app.api.v1.batch import router as batch_router

    # P3 routers
    from app.api.v1.claims import router as claims_router
    from app.api.v1.collections import router as collections_router
    from app.api.v1.cross_paper import router as cross_paper_router
    from app.api.v1.feeds import router as feeds_router
    from app.api.v1.figures import router as figures_router
    from app.api.v1.filters import router as filters_router
    from app.api.v1.governance import router as governance_router
    from app.api.v1.graph import router as graph_router
    from app.api.v1.imports import router as imports_router
    from app.api.v1.intelligence import router as intelligence_router
    from app.api.v1.jobs import router as jobs_router
    from app.api.v1.knowledge import router as knowledge_router
    from app.api.v1.knowledge_ext import router as knowledge_ext_router
    from app.api.v1.local_pdf import router as local_pdf_router
    from app.api.v1.papers import router as papers_router
    from app.api.v1.quality import router as quality_router
    from app.api.v1.researchers import router as researchers_router
    from app.api.v1.resolve import router as resolve_router
    from app.api.v1.search import router as search_router
    from app.api.v1.tags import router as tags_router
    from app.api.v1.trend_ext import router as trend_ext_router
    from app.api.v1.trends import router as trends_router
    from app.api.v1.writing import router as writing_router

    app.include_router(papers_router, prefix="/api/v1")
    app.include_router(imports_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(feeds_router, prefix="/api/v1")
    app.include_router(collections_router, prefix="/api/v1")
    app.include_router(tags_router, prefix="/api/v1")
    app.include_router(graph_router, prefix="/api/v1")
    app.include_router(governance_router, prefix="/api/v1")
    app.include_router(intelligence_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(agent_services_router, prefix="/api/v1")
    app.include_router(api_keys_router, prefix="/api/v1")
    app.include_router(answers_router, prefix="/api/v1")
    app.include_router(resolve_router, prefix="/api/v1")
    app.include_router(filters_router, prefix="/api/v1")
    app.include_router(local_pdf_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(ragflow_router.router, prefix="/api/v1")
    app.include_router(trends_router, prefix="/api/v1")
    app.include_router(trend_ext_router, prefix="/api/v1")
    app.include_router(writing_router, prefix="/api/v1")
    app.include_router(alerts_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(batch_router, prefix="/api/v1")
    # P3 routers
    app.include_router(claims_router, prefix="/api/v1")
    app.include_router(cross_paper_router, prefix="/api/v1")
    app.include_router(figures_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(knowledge_ext_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    # Content/MinerU router
    from app.api.v1.content import router as content_router

    app.include_router(content_router, prefix="/api/v1")
    # Analytics router
    from app.api.v1.analytics import router as analytics_router

    app.include_router(analytics_router, prefix="/api/v1")
    # Researcher analytics router
    app.include_router(researchers_router, prefix="/api/v1")
    # Batch 6: Collaboration & Experiments
    from app.api.v1.collaboration import router as collaboration_router
    from app.api.v1.experiments import router as experiments_router

    app.include_router(collaboration_router, prefix="/api/v1")
    app.include_router(experiments_router, prefix="/api/v1")
    # Admin + SSE (Features 7/8/9/25/26/35/42)
    from app.api.v1.admin import router as admin_router
    from app.api.v1.sse import router as sse_router

    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(sse_router, prefix="/api/v1")
    # RAGFlow evaluation / observability
    from app.api.v1.evaluation import router as eval_router

    app.include_router(eval_router, prefix="/api/v1")
    # Translation proxy (keeps API key server-side)
    from app.api.v1.translate import router as translate_router

    app.include_router(translate_router, prefix="/api/v1")

    # OpenAlex search & relation graph
    from app.api.v1.openalex import router as openalex_router

    app.include_router(openalex_router, prefix="/api/v1")

    # DeepXiv paper search & progressive reading
    from app.api.v1.deepxiv import router as deepxiv_router

    app.include_router(deepxiv_router, prefix="/api/v1")

    # User preferences & profile
    from app.api.v1.users import router as users_router

    app.include_router(users_router, prefix="/api/v1")

    # Paper QA (side panel)
    from app.api.v1.paper_qa import router as paper_qa_router

    app.include_router(paper_qa_router, prefix="/api/v1")

    # --- Health Check ---

    @app.get("/", include_in_schema=False)
    async def root():
        """Simple root entrypoint so the backend doesn't look broken in dev."""
        payload = {
            "status": "ok",
            "app": settings.app_name,
            "message": "Kaleidoscope backend is running.",
            "docs_url": "/docs",
            "health_url": "/health",
        }
        if settings.debug:
            payload["frontend_url"] = "http://localhost:3000/"
            payload["message"] = (
                "Kaleidoscope backend is running. Open the frontend at "
                "http://localhost:3000/."
            )
        return payload

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "services": {
                "database": "unknown",
            },
        }

    @app.get("/health/services")
    async def services_health():
        """Check health of all dependent services."""
        from app.services.parsing.grobid_client import GROBIDClient

        results = {}

        # PostgreSQL
        try:
            from sqlalchemy import text

            from app.dependencies import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            results["postgresql"] = "ok"
        except Exception as e:
            results["postgresql"] = f"error: {e}"

        # Redis
        try:
            import redis as redis_lib

            r = redis_lib.from_url(settings.redis_url)
            r.ping()
            results["redis"] = "ok"
        except Exception as e:
            results["redis"] = f"error: {e}"

        # GROBID
        grobid = GROBIDClient()
        results["grobid"] = "ok" if await grobid.is_alive() else "unavailable"

        return {"services": results}

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes.setdefault(
            "ApiKeyHeader",
            {"type": "apiKey", "in": "header", "name": "X-API-Key"},
        )
        security_schemes.setdefault(
            "BearerApiKey",
            {"type": "http", "scheme": "bearer"},
        )
        for path, path_item in openapi_schema.get("paths", {}).items():
            normalized_path = path.rstrip("/") or "/"
            is_protected = normalized_path in API_KEY_PROTECTED_PATHS or any(
                normalized_path == prefix or normalized_path.startswith(f"{prefix}/")
                for prefix in API_KEY_PROTECTED_PREFIXES
            )
            if not is_protected:
                continue
            for method_spec in path_item.values():
                if isinstance(method_spec, dict):
                    method_spec.setdefault(
                        "security",
                        [{"ApiKeyHeader": []}, {"BearerApiKey": []}],
                    )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    logger.info("app_created", app_name=settings.app_name)
    return app


# Create the app instance
app = create_app()
