"""Paper API routes — CRUD, import, and retrieval."""

import uuid
from datetime import UTC

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user_id, get_db
from app.models.author import PaperAuthor
from app.models.paper import Paper
from app.schemas.collection import ReadingStatusUpdate
from app.schemas.paper import (
    AuthorBrief,
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


class PaperResolveByArxivRequest(BaseModel):
    arxiv_ids: list[str]


class PaperResolveByArxivItem(BaseModel):
    paper_id: str
    arxiv_id: str
    ingestion_status: str


class PaperResolveByArxivResponse(BaseModel):
    matches: list[PaperResolveByArxivItem]


MINERU_READY_STATUSES = ("parsed", "indexed", "index_partial")


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


@router.post("/resolve-arxiv", response_model=PaperResolveByArxivResponse)
async def resolve_papers_by_arxiv(
    request: PaperResolveByArxivRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve DeepXiv arXiv IDs to local paper IDs when the paper already exists.

    Dashboard and discovery surfaces use this to prefer the local analysis page
    over the raw DeepXiv reader after a paper has entered Kaleidoscope.
    """
    normalized_ids = list(
        dict.fromkeys(aid.strip() for aid in request.arxiv_ids if aid.strip())
    )
    if not normalized_ids:
        return PaperResolveByArxivResponse(matches=[])

    result = await db.execute(
        select(Paper.id, Paper.arxiv_id, Paper.ingestion_status).where(
            Paper.deleted_at.is_(None),
            Paper.arxiv_id.in_(normalized_ids),
            or_(
                Paper.parser_version == "mineru",
                Paper.parser_version.like("mineru-%"),
            ),
            Paper.ingestion_status.in_(MINERU_READY_STATUSES),
        )
    )

    matches = [
        PaperResolveByArxivItem(
            paper_id=str(row.id),
            arxiv_id=row.arxiv_id,
            ingestion_status=row.ingestion_status,
        )
        for row in result.all()
        if row.arxiv_id
    ]
    return PaperResolveByArxivResponse(matches=matches)


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
                title=p.title or "",
                abstract=(
                    p.abstract[:300] + "..."
                    if p.abstract and len(p.abstract) > 300
                    else p.abstract
                ),
                published_at=p.published_at,
                citation_count=p.citation_count,
                has_full_text=p.has_full_text,
                ingestion_status=p.ingestion_status or "unknown",
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
        select(Paper)
        .options(
            selectinload(Paper.authors).selectinload(PaperAuthor.author),
            selectinload(Paper.venue),
        )
        .where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PAPER_NOT_FOUND",
                "message": f"Paper {paper_id} not found",
            },
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
        authors=[
            AuthorBrief(
                id=paper_author.author.id,
                display_name=paper_author.author.display_name,
                position=paper_author.position,
                is_corresponding=paper_author.is_corresponding,
            )
            for paper_author in sorted(paper.authors, key=lambda item: item.position)
            if paper_author.author is not None
        ],
        venue=paper.venue.name if paper.venue else None,
        raw_metadata=paper.raw_metadata,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
    )


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a paper."""
    from datetime import datetime

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PAPER_NOT_FOUND",
                "message": f"Paper {paper_id} not found",
            },
        )

    paper.deleted_at = datetime.now(UTC)
    return {"status": "deleted", "paper_id": str(paper_id)}


# ─── Reading Status (P1) ─────────────────────────────────────────


@router.patch("/{paper_id}/reading-status")
async def update_reading_status(
    paper_id: uuid.UUID,
    body: ReadingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update per-user reading status for a paper."""
    from app.services.collection_service import ReadingStatusService

    # Verify paper exists
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paper not found")

    svc = ReadingStatusService(db, user_id)
    status = await svc.set_status(str(paper_id), body.status)
    return {"paper_id": str(paper_id), "reading_status": status}


# ─── Tags (P1) ───────────────────────────────────────────────────


@router.post("/{paper_id}/tags/{tag_id}", status_code=201)
async def add_tag_to_paper(
    paper_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Add a tag to a paper."""
    from app.models.collection import Tag
    from app.services.collection_service import TagService

    paper_result = await db.execute(
        select(Paper.id).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    if paper_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    tag_result = await db.execute(
        select(Tag.id).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    if tag_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    svc = TagService(db, user_id)
    added = await svc.add_tag_to_paper(str(paper_id), str(tag_id))
    if not added:
        raise HTTPException(status_code=409, detail="Tag already applied")
    return {"paper_id": str(paper_id), "tag_id": str(tag_id), "status": "added"}


@router.delete("/{paper_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_paper(
    paper_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Remove a tag from a paper."""
    from app.services.collection_service import TagService

    svc = TagService(db, user_id)
    if not await svc.remove_tag_from_paper(str(paper_id), str(tag_id)):
        raise HTTPException(status_code=404, detail="Tag not found on paper")


@router.get("/{paper_id}/tags")
async def get_paper_tags(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all tags on a paper (user-scoped)."""
    from app.services.collection_service import TagService

    svc = TagService(db, user_id)
    tags = await svc.get_paper_tags(str(paper_id))
    return [{"id": str(t.id), "name": t.name, "color": t.color} for t in tags]


# ─── Export (P1) ──────────────────────────────────────────────────


@router.get("/{paper_id}/export")
async def export_paper_citation(
    paper_id: uuid.UUID,
    format: str = Query("bibtex", description="bibtex, ris, or csl_json"),
    db: AsyncSession = Depends(get_db),
):
    """Export citation for a single paper."""
    from app.services.export_service import ExportService

    svc = ExportService(db)
    content = await svc.export_papers([str(paper_id)], format=format)

    from fastapi.responses import Response

    content_types = {
        "bibtex": "application/x-bibtex",
        "ris": "application/x-research-info-systems",
        "csl_json": "application/json",
    }
    return Response(
        content=content,
        media_type=content_types.get(format, "text/plain"),
    )


# ─── Version History (Feature 2) ─────────────────────────────────


@router.get("/{paper_id}/versions")
async def get_paper_versions(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return version history for a paper from raw_metadata provenance markers."""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    raw = paper.raw_metadata or {}
    versions: list[dict] = []

    for v in raw.get("arxiv_versions") or []:
        versions.append(
            {
                "version": v.get("version"),
                "submitted": v.get("submitted"),
                "source": "arxiv",
            }
        )

    for u in raw.get("update-to") or []:
        versions.append(
            {
                "version": u.get("type"),
                "doi": u.get("DOI"),
                "updated": u.get("updated"),
                "source": "crossref",
            }
        )

    for step in raw.get("pipeline_steps") or []:
        versions.append(
            {
                "version": step.get("step"),
                "timestamp": step.get("timestamp"),
                "source": "pipeline",
            }
        )

    if not versions:
        versions = [
            {
                "version": "v1",
                "source": paper.source_type or "unknown",
                "timestamp": str(paper.created_at),
                "note": "Single ingested version.",
            }
        ]

    return {
        "paper_id": str(paper.id),
        "doi": paper.doi,
        "arxiv_id": paper.arxiv_id,
        "parser_version": paper.parser_version,
        "versions": versions,
    }


# ─── Reading Status GET (Feature 43) ─────────────────────────────


@router.get("/{paper_id}/reading-status")
async def get_reading_status(
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current reading status for a paper."""
    from app.services.collection_service import ReadingStatusService

    res = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Paper not found")

    svc = ReadingStatusService(db, user_id)
    status = await svc.get_status(str(paper_id))
    return {"paper_id": str(paper_id), "reading_status": status}


# ─── Library Deduplication (Feature 5) ───────────────────────────


@router.post("/deduplicate")
async def deduplicate_library(
    sample: int = Query(500, ge=10, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Scan the library for potential duplicate papers (DOI, arXiv ID, title fuzzy match)."""
    from app.utils.text import titles_are_similar

    res = await db.execute(
        select(Paper)
        .where(Paper.deleted_at.is_(None))
        .order_by(Paper.created_at.desc())
        .limit(sample)
    )
    papers = res.scalars().all()

    doi_map: dict[str, list[str]] = {}
    arxiv_map: dict[str, list[str]] = {}
    for p in papers:
        if p.doi:
            doi_map.setdefault(p.doi.lower(), []).append(str(p.id))
        if p.arxiv_id:
            arxiv_map.setdefault(p.arxiv_id.lower(), []).append(str(p.id))

    suspected: list[dict] = []
    for doi, ids in doi_map.items():
        if len(ids) > 1:
            suspected.append(
                {"match_type": "doi", "doi": doi, "paper_ids": ids, "confidence": 1.0}
            )
    for arxiv_id, ids in arxiv_map.items():
        if len(ids) > 1:
            suspected.append(
                {
                    "match_type": "arxiv_id",
                    "arxiv_id": arxiv_id,
                    "paper_ids": ids,
                    "confidence": 1.0,
                }
            )

    no_id = [p for p in papers if not p.doi and not p.arxiv_id and p.title]
    seen_pairs: set[frozenset] = set()
    for i, p1 in enumerate(no_id):
        for p2 in no_id[i + 1 :]:
            pk = frozenset({str(p1.id), str(p2.id)})
            if pk not in seen_pairs and titles_are_similar(
                p1.title, p2.title, threshold=0.90
            ):
                seen_pairs.add(pk)
                suspected.append(
                    {
                        "match_type": "title",
                        "titles": [p1.title, p2.title],
                        "paper_ids": [str(p1.id), str(p2.id)],
                        "confidence": 0.9,
                    }
                )

    return {
        "sample_size": len(papers),
        "duplicate_groups_found": len(suspected),
        "suspected_duplicates": suspected,
    }
