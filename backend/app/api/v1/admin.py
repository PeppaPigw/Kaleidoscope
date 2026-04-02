"""Admin API — reprocessing, LLM cost metering, weekly digest, retraction check, provenance."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.admin_service import AdminService
from app.services.quality_service import QualityService

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Feature 9: Reprocess stale papers ───────────────────────────────────────


@router.post("/reprocess")
async def reprocess_papers(
    parser_version_lt: str | None = Query(
        None,
        description="Re-queue papers whose parser_version is below this value. "
        "Omit to re-queue papers with no parser_version at all.",
    ),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Trigger re-parse for papers with an outdated (or missing) parser version."""
    svc = AdminService(db)
    return await svc.reprocess_stale_papers(
        parser_version_lt=parser_version_lt,
        limit=limit,
    )


# ── Feature 35: LLM cost metering ───────────────────────────────────────────


@router.get("/costs")
async def get_llm_costs(db: AsyncSession = Depends(get_db)):
    """Return accumulated LLM call counts, token usage, and estimated costs."""
    svc = AdminService(db)
    return await svc.get_llm_costs()


# ── Feature 26: Weekly digest ───────────────────────────────────────────────


@router.get("/digest/weekly")
async def get_weekly_digest(
    weeks_back: int = Query(1, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
):
    """Weekly new-papers digest: counts, top keywords, and citation highlights."""
    svc = AdminService(db)
    return await svc.get_weekly_digest(weeks_back=weeks_back)


# ── Feature 7: Retraction check ─────────────────────────────────────────────


@router.post("/papers/{paper_id}/retraction-check")
async def retraction_check(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Check CrossRef for retraction status of a paper by its DOI."""
    svc = QualityService(db)
    return await svc.retraction_check(str(paper_id))


# ── Feature 8: Field provenance ─────────────────────────────────────────────


@router.get("/papers/{paper_id}/provenance")
async def get_provenance(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return field-level provenance chain (source, confidence, timestamp)."""
    svc = QualityService(db)
    result = await svc.get_provenance(str(paper_id))
    return result


# ── Feature 25: Library retraction stats ────────────────────────────────────


@router.get("/retraction-stats")
async def retraction_stats(
    sample: int = Query(
        100,
        ge=1,
        le=500,
        description="How many recent papers to sample for retraction status.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Scan a sample of library papers for retraction status via CrossRef.

    This is intentionally rate-limited to *sample* papers per call to avoid
    hammering the CrossRef API.  Schedule this nightly in production.
    """
    from sqlalchemy import select as sa_select

    from app.models.paper import Paper

    result = await db.execute(
        sa_select(Paper)
        .where(Paper.deleted_at.is_(None), Paper.doi.isnot(None))
        .order_by(Paper.created_at.desc())
        .limit(sample)
    )
    papers = result.scalars().all()

    svc = QualityService(db)
    results = []
    retracted_count = 0
    error_count = 0

    for paper in papers:
        check = await svc.retraction_check(str(paper.id))
        status = check.get("status")
        if status == "retracted":
            retracted_count += 1
        elif status in ("error", "crossref_error"):
            error_count += 1
        results.append(
            {
                "paper_id": str(paper.id),
                "doi": paper.doi,
                "is_retracted": check.get("is_retracted"),
                "status": status,
            }
        )

    return {
        "sample_size": len(results),
        "retracted_count": retracted_count,
        "error_count": error_count,
        "results": results,
    }
