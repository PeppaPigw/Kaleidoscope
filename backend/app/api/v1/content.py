"""Content API — paper content retrieval and URL-based import.

Provides:
- GET /papers/{id}/content — retrieve markdown content + metadata
- POST /papers/import-url — import paper from URL via MinerU
- POST /papers/{id}/reparse — re-parse existing paper via MinerU
"""

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/papers", tags=["content"])


def _fire_analysis_bg(paper_id: str) -> None:
    """Fire-and-forget: deep-analyse a single paper, then auto-generate overview image."""
    async def _run():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.models.author import PaperAuthor
        from app.services.analysis.paper_analyst import PaperAnalystService
        from app.services.analysis.overview_image_service import OverviewImageService
        from sqlalchemy.orm import selectinload
        from datetime import datetime, timezone

        # ── Step 1: Deep analysis ──────────────────────────────────────────
        paper_title = ""
        analysis_text = ""
        try:
            async with async_session_factory() as db:
                r = await db.execute(
                    select(Paper).where(Paper.id == paper_id)
                    .options(selectinload(Paper.authors).selectinload(PaperAuthor.author))
                )
                paper = r.scalar_one_or_none()
                if paper and not paper.deep_analysis:
                    svc = PaperAnalystService(db)
                    result = await svc.analyse_and_persist(paper, db)
                    await db.commit()
                    await svc.close()
                    if result.get("status") == "ok":
                        paper_title = paper.title
                        analysis_text = result.get("analysis", "")
                elif paper and paper.deep_analysis and paper.deep_analysis.get("status") == "ok":
                    # Analysis already done; still proceed to image if missing
                    paper_title = paper.title
                    analysis_text = paper.deep_analysis.get("analysis", "")
        except Exception:
            pass  # analysis is best-effort

        # ── Step 2: Overview image (only if analysis produced text) ────────
        if not paper_title or not analysis_text.strip():
            return

        img_svc = OverviewImageService()
        try:
            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if not paper:
                    return
                # Skip if image already exists
                if paper.overview_image and paper.overview_image.get("status") == "ok":
                    return
                paper.overview_image = {"status": "generating"}
                await db.commit()

            url = await img_svc.generate(paper_title, analysis_text)

            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if paper:
                    paper.overview_image = {"status": "ok", "url": url}
                    paper.overview_image_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception as exc:
            try:
                async with async_session_factory() as db:
                    r = await db.execute(select(Paper).where(Paper.id == paper_id))
                    paper = r.scalar_one_or_none()
                    if paper:
                        paper.overview_image = {"status": "error", "error": str(exc)[:300]}
                        await db.commit()
            except Exception:
                pass
        finally:
            await img_svc.close()

    asyncio.create_task(_run())


def _fire_label_bg(paper_id: str) -> None:
    """Fire-and-forget: label a single paper in the background after import/reparse."""
    async def _run():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.analysis.labeling_service import LabelingService
        try:
            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if paper and not paper.paper_labels:
                    svc = LabelingService(db)
                    await svc.label_paper(paper)
                    await db.commit()
                    await svc.close()
        except Exception:
            pass  # labeling is best-effort; don't crash import flow

    asyncio.create_task(_run())


def _normalize_record_list(value: object) -> list[dict]:
    """Return only list-shaped JSON records expected by the content response.

    Historical data may contain MinerU layout dicts in `parsed_figures`.
    The content API should degrade gracefully instead of crashing on those rows.
    """
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


class ImportUrlRequest(BaseModel):
    url: str
    title: str | None = None
    is_html: bool = False


class ReparseRequest(BaseModel):
    url: str | None = None
    is_html: bool | None = None  # None = auto-detect from stored URL metadata


class ContentResponse(BaseModel):
    paper_id: str
    title: str | None
    abstract: str | None
    has_full_text: bool
    markdown: str
    format: str  # "markdown", "reconstructed", "abstract_only", "metadata_only"
    remote_urls: list[dict] | None = None
    markdown_provenance: dict | None = None
    sections: list[dict] = []
    figures: list[dict] = []


class ImportUrlResponse(BaseModel):
    paper_id: str
    title: str
    status: str
    error: str | None = None
    markdown_length: int | None = None
    sections: int | None = None
    references: int | None = None


@router.get("/{paper_id}/content", response_model=ContentResponse)
async def get_paper_content(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paper content as markdown + structured metadata.

    Returns the full markdown text, sections, and provenance.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Build content response with fallback chain
    sections = _normalize_record_list(paper.parsed_sections)
    figures = _normalize_record_list(paper.parsed_figures)
    md = paper.full_text_markdown or ""
    abs_len = len(paper.abstract or "")

    if md and abs_len > 0 and len(md) >= abs_len * 3:
        # Real full-text: at least 3× the abstract length
        markdown = md
        fmt = "markdown"
    elif md and abs_len == 0 and len(md) > 2000:
        # No abstract reference — trust it if it's reasonably long
        markdown = md
        fmt = "markdown"
    elif sections:
        # Reconstruct from parsed_sections
        md_parts = []
        for sec in sections:
            level = sec.get("level", 1)
            heading = sec.get("title") or sec.get("heading", "")
            md_parts.append(f"{'#' * level} {heading}\n")
            for p in sec.get("paragraphs", []):
                md_parts.append(p + "\n")
            md_parts.append("")
        markdown = "\n".join(md_parts)
        fmt = "reconstructed"
    elif paper.abstract:
        markdown = f"# {paper.title}\n\n{paper.abstract}"
        fmt = "abstract_only"
    else:
        markdown = f"# {paper.title}\n\n*No full text available.*"
        fmt = "metadata_only"

    return ContentResponse(
        paper_id=str(paper.id),
        title=paper.title,
        abstract=paper.abstract,
        has_full_text=fmt == "markdown",
        markdown=markdown,
        format=fmt,
        remote_urls=paper.remote_urls,
        markdown_provenance=paper.markdown_provenance,
        sections=sections,
        figures=figures,
    )


@router.post("/import-url", response_model=ImportUrlResponse, status_code=201)
async def import_from_url(
    req: ImportUrlRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import a paper from URL using MinerU for content extraction.

    Creates a new paper record and extracts content as markdown.
    Raises HTTP 502 if MinerU extraction fails.
    """
    from app.models.paper import Paper
    from app.services.parsing.mineru_service import MinerUParsingService
    from app.utils.doi import extract_doi_from_url

    # Try to extract DOI from URL
    doi = extract_doi_from_url(req.url)

    # Check for duplicates
    if doi:
        existing = await db.execute(
            select(Paper).where(Paper.doi == doi, Paper.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Paper with DOI {doi} already exists",
            )

    # Create paper record
    paper = Paper(
        title=req.title or f"Importing from {req.url[:60]}...",
        doi=doi,
        source_type="remote",
        ingestion_status="importing",
        remote_urls=[
            {
                "url": req.url,
                "source": "user_import",
                "type": "html" if req.is_html else "pdf",
            }
        ],
    )
    db.add(paper)
    await db.flush()

    # Parse via MinerU
    svc = MinerUParsingService(db)
    try:
        result = await svc.parse_from_url(
            paper_id=str(paper.id),
            url=req.url,
            is_html=req.is_html,
        )
    finally:
        await svc.close()

    # Propagate parse failures as HTTP errors
    if result.get("status") == "error":
        # NOTE: Intentional explicit commit — saves the paper record and failure
        # state before raising, so the import attempt is traceable even on error.
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "MinerU extraction failed"),
        )

    # NOTE: Intentional explicit commit for import completion.
    await db.commit()

    # Fire labeling + deep analysis in the background (non-blocking)
    _fire_label_bg(str(paper.id))
    _fire_analysis_bg(str(paper.id))
    _fire_links_bg(str(paper.id), paper.title)

    return ImportUrlResponse(
        paper_id=str(paper.id),
        title=paper.title,
        status=result["status"],
        markdown_length=result.get("markdown_length"),
        sections=result.get("sections"),
        references=result.get("references"),
    )


@router.post("/{paper_id}/reparse", response_model=ImportUrlResponse)
async def reparse_paper(
    paper_id: uuid.UUID,
    req: ReparseRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-parse an existing paper via MinerU.

    Uses the paper's stored URL or a provided override URL.
    Auto-detects is_html from stored URL metadata if not explicitly set.
    """
    from app.models.paper import Paper
    from app.services.parsing.mineru_service import MinerUParsingService

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Determine URL and is_html
    url = req.url
    is_html = req.is_html

    if not url and paper.remote_urls:
        stored = paper.remote_urls[0]
        url = stored.get("url")
        # Auto-detect is_html from stored metadata if not explicitly set
        if is_html is None:
            is_html = stored.get("type") == "html"

    if not url:
        raise HTTPException(
            status_code=400,
            detail="No URL available for reparsing. Provide a URL in the request.",
        )

    if is_html is None:
        is_html = False

    svc = MinerUParsingService(db)
    try:
        parse_result = await svc.parse_from_url(
            paper_id=str(paper_id),
            url=url,
            is_html=is_html,
        )
    finally:
        await svc.close()

    # Propagate parse failures as HTTP errors
    if parse_result.get("status") == "error":
        # NOTE: Intentional explicit commit — saves the paper record and failure
        # state before raising, so the import attempt is traceable even on error.
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=parse_result.get("error", "MinerU extraction failed"),
        )

    # NOTE: Intentional explicit commit for import completion.
    await db.commit()

    # Fire labeling + deep analysis in the background (non-blocking)
    _fire_label_bg(str(paper_id))
    _fire_analysis_bg(str(paper_id))
    _fire_links_bg(str(paper_id), paper.title)

    return ImportUrlResponse(
        paper_id=str(paper_id),
        title=paper.title,
        status=parse_result["status"],
        markdown_length=parse_result.get("markdown_length"),
        sections=parse_result.get("sections"),
        references=parse_result.get("references"),
    )


class LabelResponse(BaseModel):
    paper_id: str
    labels: dict
    labeled_at: str | None = None
    text_source: str  # "full_text", "abstract_only", "unavailable"


@router.get("/{paper_id}/labels", response_model=LabelResponse)
async def get_paper_labels(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return existing taxonomy labels for a paper (does not trigger LLM call)."""
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.paper_labels:
        raise HTTPException(
            status_code=404,
            detail="Labels not generated yet. POST to /labels to generate.",
        )
    return LabelResponse(
        paper_id=str(paper.id),
        labels=paper.paper_labels,
        labeled_at=paper.paper_labels_at.isoformat() if paper.paper_labels_at else None,
        text_source=(
            "full_text"
            if paper.has_full_text
            else ("abstract_only" if paper.abstract else "unavailable")
        ),
    )


@router.post("/{paper_id}/labels", response_model=LabelResponse)
async def generate_paper_labels(
    paper_id: uuid.UUID,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate (or regenerate) taxonomy labels for a paper via LLM.

    Uses full text when available, falls back to abstract.
    Set ?force=true to re-label an already-labeled paper.
    """
    from app.models.paper import Paper
    from app.services.analysis.labeling_service import LabelingService
    from app.services.extraction.chunker import TextChunker

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    fulltext = TextChunker.prepare_paper_text(paper)
    text_source = (
        "full_text"
        if (paper.has_full_text and len(fulltext) > len(paper.abstract or "") * 2)
        else ("abstract_only" if paper.abstract else "unavailable")
    )

    svc = LabelingService(db)
    try:
        labels = await svc.label_paper(paper, force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Labeling failed: {exc}")
    finally:
        await svc.close()

    await db.commit()

    return LabelResponse(
        paper_id=str(paper.id),
        labels=labels,
        labeled_at=paper.paper_labels_at.isoformat() if paper.paper_labels_at else None,
        text_source=text_source,
    )


@router.get("/{paper_id}/deep-analysis")
async def get_deep_analysis(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return deep LLM analysis for a paper."""
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.deep_analysis or paper.deep_analysis.get("status") != "ok":
        raise HTTPException(status_code=404, detail="Deep analysis not available")

    return {
        "paper_id": str(paper.id),
        "analysis": paper.deep_analysis.get("analysis", ""),
        "generated_at": paper.deep_analysis.get("generated_at"),
        "model": paper.deep_analysis.get("model"),
        "fulltext_chars": paper.deep_analysis.get("fulltext_chars"),
    }


@router.get("/{paper_id}/overview-image")
async def get_overview_image(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the 一图速览 overview image record for a paper."""
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    if not paper.overview_image:
        raise HTTPException(status_code=404, detail="Overview image not generated yet")
    return {
        "paper_id": str(paper.id),
        **paper.overview_image,
        "generated_at": paper.overview_image_at.isoformat() if paper.overview_image_at else None,
    }


def _fire_overview_image_only_bg(paper_id: str, paper_title: str, analysis_text: str) -> None:
    """Fire-and-forget: generate overview image only (analysis already done)."""
    async def _run():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.analysis.overview_image_service import OverviewImageService
        from datetime import datetime, timezone
        svc = OverviewImageService()
        try:
            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if not paper:
                    return
                paper.overview_image = {"status": "generating"}
                await db.commit()

            url = await svc.generate(paper_title, analysis_text)

            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if paper:
                    paper.overview_image = {"status": "ok", "url": url}
                    paper.overview_image_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception as exc:
            try:
                async with async_session_factory() as db:
                    r = await db.execute(select(Paper).where(Paper.id == paper_id))
                    paper = r.scalar_one_or_none()
                    if paper:
                        paper.overview_image = {"status": "error", "error": str(exc)[:300]}
                        await db.commit()
            except Exception:
                pass
        finally:
            await svc.close()

    asyncio.create_task(_run())


@router.post("/{paper_id}/overview-image", status_code=202)
async def generate_overview_image(
    paper_id: uuid.UUID,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger 一图速览 poster generation (or regeneration with ?force=true).

    Under normal flow this runs automatically after deep analysis.
    Uses paper.deep_analysis["analysis"] as content.
    Fires generation in the background; poll GET /overview-image for status.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.deep_analysis or paper.deep_analysis.get("status") != "ok":
        raise HTTPException(
            status_code=422,
            detail="Deep analysis not available. Generate deep analysis first.",
        )

    existing = paper.overview_image or {}
    if not force and existing.get("status") in ("ok", "generating"):
        return {
            "paper_id": str(paper_id),
            "status": existing["status"],
            "url": existing.get("url"),
            "message": "Already generated or in progress. Use ?force=true to regenerate.",
        }

    analysis_text = paper.deep_analysis.get("analysis", "")
    if not analysis_text.strip():
        raise HTTPException(status_code=422, detail="Deep analysis text is empty")

    _fire_overview_image_only_bg(str(paper_id), paper.title, analysis_text)
    return {"paper_id": str(paper_id), "status": "generating"}


@router.get("/{paper_id}/deep-analysis-zh")
async def get_deep_analysis_zh(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return Chinese translation of deep analysis for a paper."""
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    zh = paper.deep_analysis_zh or {}
    if zh.get("status") != "ok":
        raise HTTPException(
            status_code=404,
            detail=zh.get("status", "not_available"),
        )
    return {
        "paper_id": str(paper.id),
        "analysis": zh.get("analysis", ""),
        "translated_at": zh.get("translated_at"),
    }


def _fire_links_bg(paper_id: str, title: str) -> None:
    """Fire-and-forget: fetch AI paper links for a newly imported paper."""
    async def _run():
        from app.dependencies import async_session_factory
        from app.models.paper import Paper
        from app.services.analysis.links_service import LinksService
        from datetime import datetime, timezone

        if not title.strip():
            return
        try:
            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if not paper:
                    return
                if (paper.paper_links or {}).get("status") in ("ok", "fetching"):
                    return
                paper.paper_links = {"status": "fetching"}
                paper.paper_links_at = datetime.now(timezone.utc)
                await db.commit()

            async with LinksService() as svc:
                links = await svc.fetch_links(title)

            links_data = {
                "status": "ok",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                **links,
            }
        except Exception as exc:
            links_data = {"status": "error", "error": str(exc)[:300]}

        try:
            async with async_session_factory() as db:
                r = await db.execute(select(Paper).where(Paper.id == paper_id))
                paper = r.scalar_one_or_none()
                if paper:
                    paper.paper_links = links_data
                    paper.paper_links_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception:
            pass

    asyncio.create_task(_run())


@router.get("/{paper_id}/links")
async def get_paper_links(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return AI-fetched supplementary links for a paper."""
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    pl = paper.paper_links or {}
    status = pl.get("status", "not_started")
    if status != "ok":
        raise HTTPException(status_code=404, detail=status)
    return {
        "paper_id": str(paper.id),
        "venue": pl.get("venue"),
        "code_url": pl.get("code_url"),
        "dataset_urls": pl.get("dataset_urls"),
        "model_weights_url": pl.get("model_weights_url"),
        "project_page_url": pl.get("project_page_url"),
        "related_links": pl.get("related_links") or {},
        "fetched_at": pl.get("fetched_at"),
    }


@router.get("/{paper_id}/import-status")
async def get_import_status(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return current ingestion status for a paper.

    Clients can poll this after POST /papers/import-url to track progress.
    Status values: 'pending', 'importing', 'parsed', 'ready', 'error'.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {
        "paper_id": str(paper.id),
        "title": paper.title,
        "ingestion_status": paper.ingestion_status,
        "has_full_text": paper.has_full_text,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
        "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
        "error_message": (paper.raw_metadata or {}).get("import_error"),
    }
