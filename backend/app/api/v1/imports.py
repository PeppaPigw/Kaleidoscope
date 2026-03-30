"""Import status tracking API — poll ingestion job progress."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.paper import Paper

router = APIRouter(prefix="/imports", tags=["imports"])

TERMINAL_IMPORT_STATUSES = {
    "indexed",
    "index_partial",
    "index_failed",
    "parse_failed",
    "failed",
}


@router.get("/status/{doi_or_url:path}")
async def get_import_status(
    doi_or_url: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Poll the ingestion status of a paper by DOI or stored source URL.

    Clients should poll this endpoint every 2s while status is non-terminal.
    """
    stmt = (
        select(Paper)
        .where(
            Paper.deleted_at.is_(None),
            or_(
                Paper.doi == doi_or_url,
                cast(Paper.remote_urls, String).contains(doi_or_url),
            ),
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"No paper found for: {doi_or_url}",
            },
        )

    return {
        "paper_id": str(paper.id),
        "doi": paper.doi,
        "title": paper.title,
        "ingestion_status": paper.ingestion_status,
        "completed": paper.ingestion_status in TERMINAL_IMPORT_STATUSES,
        "has_fulltext": paper.has_full_text,
    }


@router.get("/recent")
async def recent_imports(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Return the most recently ingested or updated papers with their status."""
    stmt = (
        select(
            Paper.id,
            Paper.title,
            Paper.doi,
            Paper.ingestion_status,
            Paper.updated_at,
        )
        .where(Paper.deleted_at.is_(None))
        .order_by(desc(Paper.updated_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()
    return {
        "imports": [
            {
                "paper_id": str(r.id),
                "title": r.title,
                "doi": r.doi,
                "ingestion_status": r.ingestion_status,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    }
