"""DeepXiv paper search, progressive reading, trending, and research agent."""

import asyncio
import uuid as _uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.deepxiv import DeepXivAgentRequest
from app.services.deepxiv_service import get_deepxiv_service

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/deepxiv", tags=["deepxiv"])
DB_SESSION = Depends(get_db)
CURRENT_USER_ID = Depends(get_current_user_id)


class BookmarkRequest(BaseModel):
    collection_id: str


class DeepXivRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    size: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    search_mode: str = Field(default="hybrid", pattern="^(bm25|vector|hybrid)$")
    bm25_weight: float = Field(default=0.5, ge=0, le=1)
    vector_weight: float = Field(default=0.5, ge=0, le=1)
    categories: list[str] | None = None
    authors: list[str] | None = None
    min_citation: int | None = Field(default=None, ge=0)
    date_from: str | None = Field(default=None, description="YYYY-MM-DD")
    date_to: str | None = Field(default=None, description="YYYY-MM-DD")


# ── Search ────────────────────────────────────────────


@router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    size: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search_mode: str = Query("hybrid", description="bm25, vector, or hybrid"),
    bm25_weight: float = Query(0.5, ge=0, le=1),
    vector_weight: float = Query(0.5, ge=0, le=1),
    categories: str | None = Query(
        None, description="Comma-separated arXiv categories"
    ),
    authors: str | None = Query(None, description="Comma-separated author names"),
    min_citation: int | None = Query(None, ge=0),
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
):
    """Search arXiv papers via DeepXiv (hybrid / BM25 / vector)."""
    svc = get_deepxiv_service()
    cats = (
        [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    )
    auths = [a.strip() for a in authors.split(",") if a.strip()] if authors else None
    return await svc.search(
        q,
        size,
        offset,
        search_mode,
        bm25_weight,
        vector_weight,
        cats,
        auths,
        min_citation,
        date_from,
        date_to,
    )


@router.post("/retrieve")
async def retrieve_papers(body: DeepXivRetrieveRequest):
    """Search arXiv papers via the upstream DeepXIV retrieve API using a JSON body."""
    svc = get_deepxiv_service()
    return await svc.search(
        body.query,
        body.size,
        body.offset,
        body.search_mode,
        body.bm25_weight,
        body.vector_weight,
        body.categories,
        body.authors,
        body.min_citation,
        body.date_from,
        body.date_to,
    )


# ── Paper: progressive reading ────────────────────────


@router.get("/papers/{arxiv_id}/head")
async def paper_head(arxiv_id: str):
    """Full metadata with section-level TLDRs and token counts."""
    svc = get_deepxiv_service()
    result = await svc.head(arxiv_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Paper not found: {arxiv_id}")
    return result


@router.get("/papers/{arxiv_id}/brief")
async def paper_brief(arxiv_id: str):
    """Quick paper snapshot: title, TLDR, keywords, citations, GitHub URL."""
    svc = get_deepxiv_service()
    result = await svc.brief(arxiv_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Paper not found: {arxiv_id}")
    return result


@router.get("/papers/{arxiv_id}/section")
async def paper_section(
    arxiv_id: str,
    name: str = Query(..., min_length=1, description="Section name (case-insensitive)"),
):
    """Read a specific paper section by name."""
    svc = get_deepxiv_service()
    content = await svc.section(arxiv_id, name)
    return {"arxiv_id": arxiv_id, "section_name": name, "content": content}


@router.get("/papers/{arxiv_id}/preview")
async def paper_preview(
    arxiv_id: str,
    characters: int = Query(10000, ge=100, le=100000),
):
    """Preview a configurable number of characters from the paper."""
    svc = get_deepxiv_service()
    return await svc.preview(arxiv_id, characters=characters)


@router.get("/papers/{arxiv_id}/raw")
async def paper_raw(arxiv_id: str):
    """Full paper text in Markdown."""
    svc = get_deepxiv_service()
    text = await svc.raw(arxiv_id)
    return {"arxiv_id": arxiv_id, "content": text}


@router.get("/papers/{arxiv_id}/json")
async def paper_json(arxiv_id: str):
    """Complete structured JSON representation."""
    svc = get_deepxiv_service()
    return await svc.json(arxiv_id)


@router.get("/papers/{arxiv_id}/markdown-url")
async def paper_markdown_url(arxiv_id: str):
    """Public HTML URL on arxiv.org."""
    svc = get_deepxiv_service()
    url = await svc.markdown_url(arxiv_id)
    return {"arxiv_id": arxiv_id, "url": url}


@router.get("/papers/{arxiv_id}/social-impact")
async def paper_social_impact(arxiv_id: str):
    """Social media propagation metrics (tweets, likes, views)."""
    svc = get_deepxiv_service()
    result = await svc.social_impact(arxiv_id)
    if result is None:
        return {"arxiv_id": arxiv_id, "message": "No social impact data available"}
    return result


# ── PMC ───────────────────────────────────────────────


@router.get("/pmc/{pmc_id}/head")
async def pmc_head(pmc_id: str):
    """PubMed Central paper metadata."""
    svc = get_deepxiv_service()
    result = await svc.pmc_head(pmc_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"PMC paper not found: {pmc_id}")
    return result


@router.get("/pmc/{pmc_id}/full")
async def pmc_full(pmc_id: str):
    """PubMed Central complete structured JSON."""
    svc = get_deepxiv_service()
    return await svc.pmc_full(pmc_id)


@router.get("/pmc/{pmc_id}/json")
async def pmc_json(pmc_id: str):
    """PubMed Central complete structured JSON; upstream-compatible alias."""
    svc = get_deepxiv_service()
    return await svc.pmc_full(pmc_id)


@router.get("/usage")
async def usage_stats(days: int = Query(7, ge=1, le=30)):
    """DeepXIV token usage statistics proxied through Kaleidoscope."""
    svc = get_deepxiv_service()
    return await svc.usage(days=days)


# ── Trending ──────────────────────────────────────────


async def _local_trending_fallback(
    db: AsyncSession,
    *,
    days: int,
    limit: int,
) -> dict:
    """Fallback discovery feed when upstream trending is empty.

    The DeepXiv upstream endpoint occasionally returns an empty trending list
    even when the rest of the API is healthy. In that case, expose a
    deterministic local-library fallback instead of rendering a blank page.
    """
    from app.models.paper import Paper

    result = await db.execute(
        select(Paper)
        .where(
            Paper.deleted_at.is_(None),
            Paper.arxiv_id.is_not(None),
        )
        .order_by(
            Paper.citation_count.desc().nullslast(),
            Paper.published_at.desc().nullslast(),
            Paper.created_at.desc(),
        )
        .limit(limit)
    )
    papers = result.scalars().all()

    return {
        "days": days,
        "generated_at": datetime.now(UTC).isoformat(),
        "papers": [
            {
                "arxiv_id": paper.arxiv_id,
                "rank": index + 1,
                "title": paper.title,
                "citation_count": paper.citation_count or 0,
                "publish_at": (
                    paper.published_at.isoformat() if paper.published_at else None
                ),
                "source": "local_fallback",
            }
            for index, paper in enumerate(papers)
            if paper.arxiv_id
        ],
        "total": len(papers),
        "source": "local-fallback",
        "message": (
            "DeepXiv trending feed is currently empty. "
            "Showing high-signal papers from your local library instead."
        ),
    }


@router.get("/trending")
async def trending_papers(
    days: int = Query(7, description="Time window: 7, 14, or 30"),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = DB_SESSION,
):
    """Trending arXiv papers (no token required)."""
    if days not in (7, 14, 30):
        raise HTTPException(status_code=400, detail="days must be 7, 14, or 30")
    svc = get_deepxiv_service()
    result = await svc.trending(days=days, limit=limit)

    if result.get("papers"):
        result["source"] = "deepxiv"
        return result

    fallback = await _local_trending_fallback(db, days=days, limit=limit)
    if fallback.get("papers"):
        logger.warning(
            "deepxiv_trending_empty_using_local_fallback",
            days=days,
            limit=limit,
            fallback_total=fallback.get("total", 0),
        )
        return fallback

    result["source"] = "deepxiv-empty"
    result["message"] = "DeepXiv trending feed returned no papers."
    return result


# ── Trending Ingest ───────────────────────────────────


@router.post("/trending/ingest")
async def ingest_trending(
    days: int = Query(7, description="Time window: 7, 14, or 30"),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = DB_SESSION,
):
    """Fetch trending papers and queue NEW ones for local processing.

    Papers already in the local DB are skipped (deduplicated by arxiv_id).
    Returns { queued, skipped, total, arxiv_ids_queued }.
    """
    from app.models.paper import Paper
    from app.tasks.ingest_tasks import ingest_paper

    if days not in (7, 14, 30):
        raise HTTPException(status_code=400, detail="days must be 7, 14, or 30")

    svc = get_deepxiv_service()
    trending_resp = await svc.trending(days=days, limit=limit)

    papers_list = trending_resp.get("papers", [])
    arxiv_ids: list[str] = [p["arxiv_id"] for p in papers_list if p.get("arxiv_id")]

    if not arxiv_ids:
        return {"queued": 0, "skipped": 0, "total": 0, "arxiv_ids_queued": []}

    # Check which arxiv_ids already exist locally
    result = await db.execute(
        select(Paper.arxiv_id).where(Paper.arxiv_id.in_(arxiv_ids))
    )
    existing_ids: set[str] = {row[0] for row in result.fetchall()}

    new_ids = [aid for aid in arxiv_ids if aid not in existing_ids]

    # Queue each new paper for ingestion
    for arxiv_id in new_ids:
        try:
            ingest_paper.delay(arxiv_id, "arxiv")
        except Exception:
            logger.warning("failed_to_queue_ingest", arxiv_id=arxiv_id)

    logger.info(
        "trending_ingest",
        total=len(arxiv_ids),
        queued=len(new_ids),
        skipped=len(existing_ids),
    )
    return {
        "queued": len(new_ids),
        "skipped": len(existing_ids),
        "total": len(arxiv_ids),
        "arxiv_ids_queued": new_ids,
    }


# ── Batch Ingest ──────────────────────────────────────


class BatchIngestRequest(BaseModel):
    arxiv_ids: list[str]

    @field_validator("arxiv_ids")
    @classmethod
    def validate_arxiv_ids(cls, v: list[str]) -> list[str]:
        if len(v) > 100:
            raise ValueError("Maximum 100 arxiv_ids per request")
        # Deduplicate and validate format
        seen = set()
        validated = []
        for aid in v:
            aid = aid.strip()
            if not aid:
                continue
            if len(aid) > 50:
                raise ValueError(f"arxiv_id too long: {aid[:20]}...")
            if aid in seen:
                continue
            seen.add(aid)
            validated.append(aid)
        return validated


@router.post("/papers/ingest")
async def ingest_papers_batch(
    body: BatchIngestRequest,
    db: AsyncSession = DB_SESSION,
    user_id: str = CURRENT_USER_ID,
):
    """Queue a list of arxiv_ids for local processing.

    Papers already in the local DB are skipped (deduplicated by arxiv_id).
    Returns { queued, skipped, total, arxiv_ids_queued }.
    Requires authentication.
    """
    from app.models.paper import Paper
    from app.tasks.ingest_tasks import ingest_paper

    arxiv_ids = body.arxiv_ids

    if not arxiv_ids:
        return {"queued": 0, "skipped": 0, "total": 0, "arxiv_ids_queued": []}

    # Check which arxiv_ids already exist locally
    result = await db.execute(
        select(Paper.arxiv_id).where(Paper.arxiv_id.in_(arxiv_ids))
    )
    existing_ids: set[str] = {row[0] for row in result.fetchall()}

    new_ids = [aid for aid in arxiv_ids if aid not in existing_ids]

    # Queue each new paper for ingestion
    queued_count = 0
    failed_count = 0
    for arxiv_id in new_ids:
        try:
            ingest_paper.delay(arxiv_id, "arxiv")
            queued_count += 1
        except Exception:
            logger.warning("failed_to_queue_ingest", arxiv_id=arxiv_id)
            failed_count += 1

    logger.info(
        "batch_ingest",
        user_id=user_id,
        total=len(arxiv_ids),
        queued=queued_count,
        skipped=len(existing_ids),
        failed=failed_count,
    )
    return {
        "queued": queued_count,
        "skipped": len(existing_ids),
        "failed": failed_count,
        "total": len(arxiv_ids),
        "arxiv_ids_queued": new_ids[:queued_count],
    }


# ── Web Search ────────────────────────────────────────


@router.get("/websearch")
async def web_search(q: str = Query(..., min_length=1, description="Search query")):
    """Web / scholar search (consumes 20 API credits per call)."""
    svc = get_deepxiv_service()
    return await svc.websearch(q)


# ── Semantic Scholar ──────────────────────────────────


@router.get("/semantic-scholar/{s2_id}")
async def semantic_scholar_lookup(s2_id: str):
    """Look up paper metadata by Semantic Scholar ID."""
    svc = get_deepxiv_service()
    result = await svc.semantic_scholar(s2_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"S2 paper not found: {s2_id}")
    return result


# ── Bookmark ─────────────────────────────────────────


@router.post("/papers/{arxiv_id}/bookmark", status_code=201)
async def bookmark_paper(
    arxiv_id: str,
    body: BookmarkRequest,
    db: AsyncSession = DB_SESSION,
    user_id: str = CURRENT_USER_ID,
):
    """Save a DeepXiv paper to a paper_group collection.

    Upserts a minimal paper record in the local DB (by arxiv_id),
    then adds it to the specified collection.
    """
    from app.models.paper import Paper
    from app.services.collection_service import CollectionService

    # Validate the target collection exists and belongs to the user
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(body.collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.kind != "paper_group":
        raise HTTPException(
            status_code=422, detail="Target collection must be of kind 'paper_group'"
        )

    # Fetch paper metadata from DeepXiv
    deepxiv = get_deepxiv_service()
    head = await deepxiv.head(arxiv_id)
    if head is None:
        raise HTTPException(
            status_code=404, detail=f"Paper not found on DeepXiv: {arxiv_id}"
        )

    title = head.get("title", arxiv_id)
    abstract = head.get("abstract")
    authors_raw = head.get("authors", [])
    publish_at_str = head.get("publish_at")

    # Extract author name strings
    author_names: list[str] = []
    for a in authors_raw:
        if isinstance(a, str):
            author_names.append(a)
        elif isinstance(a, dict):
            author_names.append(a.get("name", ""))

    # Upsert paper in local DB
    result = await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
    paper = result.scalar_one_or_none()

    if paper is None:
        from datetime import date as _date

        published: _date | None = None
        if publish_at_str:
            try:
                published = _date.fromisoformat(publish_at_str[:10])
            except ValueError:
                published = None

        paper = Paper(
            id=_uuid.uuid4(),
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            published_at=published,
            paper_type="preprint",
        )
        db.add(paper)
        await db.flush()

    paper_id = str(paper.id)
    added = await svc.add_papers(body.collection_id, [paper_id])

    return {
        "collection_id": body.collection_id,
        "paper_id": paper_id,
        "arxiv_id": arxiv_id,
        "title": title,
        "added": added,
    }


# ── Research Agent ────────────────────────────────────


@router.post("/agent/query")
async def agent_query(body: DeepXivAgentRequest):
    """Run a research question through the DeepXiv ReAct agent.

    Requires ``deepxiv-sdk[agent]`` to be installed.
    Uses the project-wide LLM settings from config.
    """
    try:
        from deepxiv_sdk import Agent, Reader
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail="Agent feature requires deepxiv-sdk[agent] (openai, langgraph, langchain-core)",
        ) from exc

    from app.config import settings

    reader = Reader(
        token=settings.deepxiv_token or None,
        base_url=settings.deepxiv_base_url,
    )
    agent = Agent(
        api_key=settings.llm_api_key,
        reader=reader,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        max_llm_calls=15,
        max_time_seconds=300,
        temperature=0.7,
    )

    answer = await asyncio.to_thread(
        agent.query, body.question, reset_papers=body.reset_papers
    )
    papers_loaded = len(agent.get_loaded_papers())
    return {"answer": answer, "papers_loaded": papers_loaded}
