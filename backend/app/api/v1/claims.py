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
