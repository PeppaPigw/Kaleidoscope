"""Cross-paper reasoning API — synthesis, timelines, essential papers.

P3 WS-2: §20 (#165-176)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/cross-paper", tags=["cross-paper"])


class SynthesisRequest(BaseModel):
    paper_ids: list[str]
    topic: str = "this research area"


class EssentialPapersRequest(BaseModel):
    paper_ids: list[str]
    top_k: int = 10


class BridgePapersRequest(BaseModel):
    paper_ids: list[str]


class TimelineRequest(BaseModel):
    paper_ids: list[str]


@router.post("/synthesize")
async def synthesize(
    req: SynthesisRequest,
    db: AsyncSession = Depends(get_db),
):
    """Synthesize knowledge across multiple papers."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    try:
        return await svc.synthesize(req.paper_ids, req.topic)
    finally:
        await svc.close()


@router.post("/timeline")
async def build_timeline(
    req: TimelineRequest,
    db: AsyncSession = Depends(get_db),
):
    """Build a research evolution timeline from papers."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    try:
        return await svc.build_timeline(req.paper_ids)
    finally:
        await svc.close()


@router.post("/essential-papers")
async def essential_papers(
    req: EssentialPapersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Find the minimal essential reading set using citation importance."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    return {"papers": await svc.find_essential_papers(req.paper_ids, req.top_k)}


@router.post("/bridge-papers")
async def bridge_papers(
    req: BridgePapersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Detect bridge papers connecting research communities."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    return {"papers": await svc.find_bridge_papers(req.paper_ids)}
