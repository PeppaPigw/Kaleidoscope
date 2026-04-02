"""Writing Support API — related work, bibliography, gap analysis, rebuttal.

P2 WS-3: §22 (#189-200) from FeasibilityAnalysis.md
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.writing.writing_service import WritingService

router = APIRouter(prefix="/writing", tags=["writing"])


def _raise_writing_error(result: dict) -> None:
    error = result.get("error")
    if not error:
        return
    detail = str(error)
    if "not found" in detail.lower() or detail.lower() == "no papers found":
        raise HTTPException(status_code=404, detail=detail)
    raise HTTPException(
        status_code=502,
        detail=f"Writing service error: {detail[:200]}",
    )


# ─── Schemas ─────────────────────────────────────────────────────


class RelatedWorkRequest(BaseModel):
    paper_ids: list[str]
    style: str = Field("narrative", description="narrative, thematic, or chronological")
    format: str = Field("markdown", description="markdown or latex")


class AnnotatedBibRequest(BaseModel):
    paper_ids: list[str]
    annotation_depth: str = Field("detailed", description="brief or detailed")


class GapAnalysisRequest(BaseModel):
    paper_ids: list[str]
    research_question: str


class RebuttalRequest(BaseModel):
    paper_id: str
    reviewer_comments: str


# ─── Endpoints ───────────────────────────────────────────────────


@router.post("/related-work")
async def generate_related_work(
    body: RelatedWorkRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a Related Work section from selected papers.

    Supports three writing styles:
    - **narrative**: flowing prose connecting papers
    - **thematic**: grouped by research themes
    - **chronological**: ordered by publication date

    Output in Markdown or LaTeX format.
    """
    svc = WritingService(db)
    try:
        result = await svc.generate_related_work(
            paper_ids=body.paper_ids,
            style=body.style,
            format=body.format,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/annotated-bibliography")
async def generate_annotated_bibliography(
    body: AnnotatedBibRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an annotated bibliography for selected papers.

    Each entry includes: citation, summary, evaluation, and relevance note.
    """
    svc = WritingService(db)
    try:
        result = await svc.generate_annotated_bibliography(
            paper_ids=body.paper_ids,
            annotation_depth=body.annotation_depth,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/gap-analysis")
async def analyze_research_gaps(
    body: GapAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Identify research gaps from literature relative to a research question.

    Returns structured analysis: well-covered areas, partially addressed,
    unexplored gaps, methodological gaps, and recommended directions.
    """
    svc = WritingService(db)
    try:
        result = await svc.analyze_gaps(
            paper_ids=body.paper_ids,
            research_question=body.research_question,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/rebuttal")
async def draft_rebuttal(
    body: RebuttalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Draft a point-by-point rebuttal to reviewer comments.

    Generates professional, diplomatic responses to each concern.
    """
    svc = WritingService(db)
    try:
        result = await svc.draft_rebuttal(
            paper_id=body.paper_id,
            reviewer_comments=body.reviewer_comments,
        )
        _raise_writing_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Writing service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()
