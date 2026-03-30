"""Claim extraction API — extract, list, assess atomic claims.

P3 WS-1: §17 (#129-140)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/papers/{paper_id}/extract")
async def extract_claims(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Extract atomic claims and evidence from a paper using LLM."""
    from app.services.analysis.claim_service import ClaimExtractionService

    svc = ClaimExtractionService(db)
    try:
        result = await svc.extract_claims(paper_id)
        return result
    finally:
        await svc.close()


@router.get("/papers/{paper_id}")
async def list_claims(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all extracted claims for a paper."""
    from app.services.analysis.claim_service import ClaimExtractionService

    svc = ClaimExtractionService(db)
    return {"paper_id": paper_id, "claims": await svc.list_claims(paper_id)}


@router.get("/stats")
async def claims_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return aggregate claim statistics for the evidence lab header."""
    from collections import Counter

    from sqlalchemy import func, select

    from app.models.claim import Claim, EvidenceLink

    total = await db.scalar(select(func.count()).select_from(Claim))
    rows = await db.execute(
        select(Claim.id, EvidenceLink.is_sufficient).outerjoin(
            EvidenceLink,
            EvidenceLink.claim_id == Claim.id,
        )
    )

    claim_flags: dict[str, list[bool | None]] = {}
    for claim_id, is_sufficient in rows:
        claim_flags.setdefault(str(claim_id), []).append(is_sufficient)

    by_status = Counter()
    for flags in claim_flags.values():
        if any(flag is False for flag in flags):
            by_status["disputed"] += 1
        elif any(flag is True for flag in flags):
            by_status["verified"] += 1
        else:
            by_status["unverified"] += 1

    return {
        "total_claims": total or 0,
        "by_status": dict(by_status),
    }


@router.post("/papers/{paper_id}/assess")
async def assess_evidence(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Assess evidence sufficiency for a paper's claims."""
    from app.services.analysis.claim_service import ClaimExtractionService

    svc = ClaimExtractionService(db)
    try:
        result = await svc.assess_evidence(paper_id)
        return result
    finally:
        await svc.close()
