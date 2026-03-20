"""Paper API routes — CRUD, import, and retrieval."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.paper import Paper
from app.schemas.paper import (
    BatchImportResult,
    ImportResult,
    PaperBatchImportRequest,
    PaperBriefResponse,
    PaperImportRequest,
    PaperListResponse,
    PaperResponse,
)
from app.tasks.ingest_tasks import ingest_paper

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/import", response_model=ImportResult)
async def import_paper(
    request: PaperImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Import a single paper by identifier (DOI, arXiv ID, PMID, or URL).

    Queues the paper for full ingestion pipeline:
    discovery → dedup → enrich → PDF → parse → index.
    """
    logger.info(
        "import_paper_request",
        identifier=request.identifier,
        type=request.identifier_type,
    )

    # Queue for async ingestion
    task = ingest_paper.delay(
        identifier=request.identifier,
        id_type=request.identifier_type,
    )

    return ImportResult(
        identifier=request.identifier,
        status="queued",
        message=f"Paper queued for ingestion. Task ID: {task.id}",
    )


@router.post("/batch-import", response_model=BatchImportResult)
async def batch_import_papers(
    request: PaperBatchImportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import multiple papers. Each is queued for async processing."""
    results = []
    queued = 0

    for item in request.items:
        task = ingest_paper.delay(
            identifier=item.identifier,
            id_type=item.identifier_type,
        )
        results.append(
            ImportResult(
                identifier=item.identifier,
                status="queued",
                message=f"Task ID: {task.id}",
            )
        )
        queued += 1

    return BatchImportResult(
        results=results,
        total=len(request.items),
        created=0,
        duplicates=0,
        queued=queued,
        failed=0,
    )


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="Sort field"),
    order: str = Query("desc", description="asc or desc"),
    db: AsyncSession = Depends(get_db),
):
    """List papers with pagination."""
    # Count total
    count_q = select(func.count()).select_from(Paper).where(Paper.deleted_at.is_(None))
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page
    sort_col = getattr(Paper, sort_by, Paper.created_at)
    order_fn = sort_col.desc() if order == "desc" else sort_col.asc()

    query = (
        select(Paper)
        .where(Paper.deleted_at.is_(None))
        .order_by(order_fn)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    papers = result.scalars().all()

    return PaperListResponse(
        items=[
            PaperBriefResponse(
                id=p.id,
                doi=p.doi,
                arxiv_id=p.arxiv_id,
                title=p.title,
                abstract=p.abstract[:300] + "..." if p.abstract and len(p.abstract) > 300 else p.abstract,
                published_at=p.published_at,
                citation_count=p.citation_count,
                has_full_text=p.has_full_text,
                ingestion_status=p.ingestion_status,
                created_at=p.created_at,
            )
            for p in papers
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get full paper details by ID."""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={"code": "PAPER_NOT_FOUND", "message": f"Paper {paper_id} not found"},
        )

    return PaperResponse(
        id=paper.id,
        doi=paper.doi,
        arxiv_id=paper.arxiv_id,
        pmid=paper.pmid,
        title=paper.title,
        abstract=paper.abstract,
        published_at=paper.published_at,
        paper_type=paper.paper_type,
        oa_status=paper.oa_status,
        language=paper.language,
        keywords=paper.keywords,
        citation_count=paper.citation_count,
        has_full_text=paper.has_full_text,
        ingestion_status=paper.ingestion_status,
        summary=paper.summary,
        highlights=paper.highlights,
        contributions=paper.contributions,
        limitations=paper.limitations,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a paper."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={"code": "PAPER_NOT_FOUND", "message": f"Paper {paper_id} not found"},
        )

    paper.deleted_at = datetime.now(timezone.utc)
    return {"status": "deleted", "paper_id": str(paper_id)}
