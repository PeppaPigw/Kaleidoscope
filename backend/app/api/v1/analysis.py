"""Deep Paper Analysis API — innovation, experiments, validity, comparison.

P2 WS-5: §11 (#81-88) from FeasibilityAnalysis.md
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.analysis.deep_analysis import DeepAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _raise_analysis_error(result: dict) -> None:
    error = result.get("error")
    if not error:
        return
    detail = str(error)
    if "not found" in detail.lower():
        raise HTTPException(status_code=404, detail=detail)
    raise HTTPException(
        status_code=502,
        detail=f"Analysis service error: {detail[:200]}",
    )


class CompareRequest(BaseModel):
    """Two papers to compare."""

    paper_id_a: str
    paper_id_b: str


@router.post("/papers/{paper_id}/innovation")
async def analyze_innovation(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a paper's innovation points vs. prior work.

    Uses LLM to compare the paper's contributions against its references
    and identify novel claims, methods, and approaches.

    Returns innovation points with novelty type and evidence strength.
    """
    svc = DeepAnalysisService(db)
    try:
        result = await svc.analyze_innovation(paper_id)
        _raise_analysis_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/papers/{paper_id}/extract-experiments")
async def extract_experiments(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Extract structured experiment data from a paper.

    Pulls out methods, datasets, metrics, and numerical results
    into a structured format suitable for cross-paper comparison.
    """
    svc = DeepAnalysisService(db)
    try:
        result = await svc.extract_experiments(paper_id)
        _raise_analysis_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/papers/{paper_id}/validity")
async def analyze_validity(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze validity threats and methodological rigor.

    Evaluates the paper against an 8-point checklist covering:
    statistical rigor, sample size, baselines, ablations,
    reproducibility, generalization, metrics, and confounders.

    Returns identified threats with severity levels and an overall score.
    """
    svc = DeepAnalysisService(db)
    try:
        result = await svc.analyze_validity(paper_id)
        _raise_analysis_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/papers/compare")
async def compare_papers(
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Compare two papers on methods, results, and approaches.

    Identifies shared/unique methods, compares results on common
    benchmarks, and highlights key differences.
    """
    svc = DeepAnalysisService(db)
    try:
        result = await svc.compare_papers(body.paper_id_a, body.paper_id_b)
        _raise_analysis_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Analysis service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()
