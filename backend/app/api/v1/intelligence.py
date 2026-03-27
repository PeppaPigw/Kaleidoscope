"""Paper intelligence API — similarity, reading paths, and citation timelines."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class ComparePapersRequest(BaseModel):
    paper_ids: list[str] = Field(..., min_length=2, max_length=5)


@router.get("/papers/{paper_id}/similar")
async def get_similar_papers(
    paper_id: UUID,
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return papers similar to the given root paper."""
    svc = IntelligenceService(db)
    paper = await svc._get_paper(str(paper_id))
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return await svc.get_similar_papers(str(paper_id), top_k=top_k)


@router.get("/papers/{paper_id}/reading-order")
async def get_reading_order(
    paper_id: UUID,
    max_papers: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Build a reading order from the root paper's citation neighborhood."""
    svc = IntelligenceService(db)
    return await svc.get_reading_order(str(paper_id), max_papers=max_papers)


@router.get("/papers/{paper_id}/prerequisites")
async def get_prerequisites(
    paper_id: UUID,
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return foundational prerequisites for the given paper."""
    svc = IntelligenceService(db)
    return await svc.get_prerequisites(str(paper_id), top_k=top_k)


@router.get("/papers/{paper_id}/related-pack")
async def get_related_work_pack(
    paper_id: UUID,
    max_papers: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return a related-work pack around a root paper."""
    svc = IntelligenceService(db)
    result = await svc.get_related_work_pack(str(paper_id), max_papers=max_papers)
    if result["root_paper"] is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return result


@router.get("/papers/{paper_id}/citation-timeline")
async def get_citation_timeline(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return citation counts over time for the given paper."""
    svc = IntelligenceService(db)
    result = await svc.get_citation_timeline(str(paper_id))
    if result["title"] is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return result


@router.get("/reading-path")
async def get_reading_path(
    from_id: str,
    to_id: str,
    max_hops: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Find the shortest citation path between two papers."""
    svc = IntelligenceService(db)
    return await svc.get_reading_path(from_id=from_id, to_id=to_id, max_hops=max_hops)


@router.get("/bridge-papers")
async def get_bridge_papers(
    keyword_a: str,
    keyword_b: str,
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Find papers that bridge two keyword areas."""
    svc = IntelligenceService(db)
    return await svc.get_bridge_papers(
        keyword_a=keyword_a,
        keyword_b=keyword_b,
        top_k=top_k,
    )


@router.post("/compare")
async def compare_papers(
    body: ComparePapersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compare up to five papers side by side."""
    svc = IntelligenceService(db)
    return await svc.compare_papers(body.paper_ids)


# ─── Feature 41: MCP-compatible agent summary ────────────────────

@router.get("/papers/{paper_id}/agent-summary")
async def get_agent_summary(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return a structured paper summary optimized for MCP tool consumption.

    Format mirrors the Anthropic MCP tool response schema — all fields are
    typed strings or lists for easy deserialization in LLM agent pipelines.

    Fields returned:
    - `paper_id`, `doi`, `arxiv_id`
    - `title`, `abstract_snippet` (first 400 chars)
    - `authors`, `venue`, `year`
    - `keywords`, `has_full_text`, `citation_count`
    - `oa_status`, `ingestion_status`
    - `summary`, `contributions`, `limitations`
    - `quality_score` (from QualityService)
    - `links.pdf`, `links.doi`, `links.arxiv`
    """
    from sqlalchemy import select
    from app.models.paper import Paper
    from app.services.quality_service import QualityService

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Pull quality score without hitting external APIs
    quality_svc = QualityService(db)
    q_result = await quality_svc.score_metadata(str(paper_id))
    quality_score = q_result.get("overall_score") if isinstance(q_result, dict) else None

    # Build links
    links: dict[str, str | None] = {
        "doi": f"https://doi.org/{paper.doi}" if paper.doi else None,
        "arxiv": f"https://arxiv.org/abs/{paper.arxiv_id}" if paper.arxiv_id else None,
        "pdf": None,
    }
    raw = paper.raw_metadata or {}
    links["pdf"] = raw.get("pdf_url") or raw.get("best_oa_url")

    abstract = paper.abstract or ""
    return {
        "paper_id": str(paper.id),
        "doi": paper.doi,
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "abstract_snippet": abstract[:400] + ("..." if len(abstract) > 400 else ""),
        "authors": raw.get("authors_parsed") or raw.get("authors") or [],
        "venue": raw.get("venue") or raw.get("container-title"),
        "year": paper.published_at.year if paper.published_at else None,
        "keywords": paper.keywords or [],
        "has_full_text": paper.has_full_text,
        "citation_count": paper.citation_count,
        "oa_status": paper.oa_status,
        "ingestion_status": paper.ingestion_status,
        "summary": paper.summary,
        "contributions": paper.contributions,
        "limitations": paper.limitations,
        "quality_score": quality_score,
        "links": links,
    }