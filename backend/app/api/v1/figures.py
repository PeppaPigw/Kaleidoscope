"""Figure/table intelligence API — analysis, retrieval, cross-paper aggregation.

P3 WS-3: §19 (#153-164)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/figures", tags=["figures"])


class AggregateRequest(BaseModel):
    paper_ids: list[str]


@router.post("/papers/{paper_id}/analyze")
async def analyze_figures(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Analyze and classify all figures/tables in a paper."""
    from app.services.analysis.figure_table_service import FigureTableService

    svc = FigureTableService(db)
    try:
        return await svc.analyze_figures(paper_id)
    finally:
        await svc.close()


@router.get("/papers/{paper_id}")
async def get_figures(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get previously extracted figures/tables for a paper."""
    from app.services.analysis.figure_table_service import FigureTableService

    svc = FigureTableService(db)
    return await svc.get_figures(paper_id)


@router.post("/aggregate-results")
async def aggregate_results(
    req: AggregateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Aggregate experimental results from multiple papers into a unified comparison table."""
    from app.services.analysis.figure_table_service import FigureTableService

    svc = FigureTableService(db)
    try:
        return await svc.aggregate_results(req.paper_ids)
    finally:
        await svc.close()
