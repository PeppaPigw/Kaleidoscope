"""Deep Paper Analysis API — innovation, experiments, validity, comparison.

P2 WS-5: §11 (#81-88) from FeasibilityAnalysis.md
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.analysis.deep_analysis import DeepAnalysisService
from app.services.analysis.evidence_lab_service import EvidenceLabService

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


class AnalysisFieldCompletionResponse(BaseModel):
    method: float = 0.0
    dataset: float = 0.0
    metric: float = 0.0
    numeric_value: float = 0.0


class AnalysisCoverageResponse(BaseModel):
    total_records: int = 0
    main_result_records: int = 0
    methods: int = 0
    datasets: int = 0
    metrics: int = 0
    field_completion: AnalysisFieldCompletionResponse = Field(
        default_factory=AnalysisFieldCompletionResponse
    )
    overall: float = 0.0


class AnalysisConfidenceResponse(BaseModel):
    overall: float = 0.0
    records: dict[str, float] = Field(default_factory=dict)


class AnalysisPaperInfoResponse(BaseModel):
    id: str
    title: str
    year: int | None = None
    source: str


class AnalysisMethodSummaryResponse(BaseModel):
    id: str
    name: str
    paper_id: str
    paper_title: str
    datasets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    record_count: int = 0
    main_result_count: int = 0


class AnalysisExperimentRecordResponse(BaseModel):
    id: str
    paper_id: str
    paper_title: str
    paper_year: int | None = None
    source: str
    method_name: str
    method_key: str
    dataset: str
    dataset_key: str
    metric: str
    metric_key: str
    column_key: str
    value_raw: Any | None = None
    value_display: str
    value_numeric: float | None = None
    is_main_result: bool = False
    comparison: str | None = None
    split: str | None = None
    higher_is_better: bool = True
    comparable: bool = True
    confidence: float = 0.0


class AnalysisMatrixColumnResponse(BaseModel):
    key: str
    dataset: str
    metric: str
    higher_is_better: bool = True


class AnalysisMatrixRowResponse(BaseModel):
    id: str
    paper_id: str
    paper_title: str
    method: str
    source: str
    metrics: dict[str, str] = Field(default_factory=dict)
    numeric_metrics: dict[str, float | None] = Field(default_factory=dict)
    best_metrics: list[str] = Field(default_factory=list)
    is_best: bool = False
    record_ids: list[str] = Field(default_factory=list)
    confidence: float | None = None
    datasets: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class AnalysisMatrixResponse(BaseModel):
    columns: list[AnalysisMatrixColumnResponse] = Field(default_factory=list)
    metric_names: list[str] = Field(default_factory=list)
    rows: list[AnalysisMatrixRowResponse] = Field(default_factory=list)
    best_by_column: dict[str, str] = Field(default_factory=dict)


class ExperimentExtractionResponse(BaseModel):
    paper_id: str
    title: str
    paper: AnalysisPaperInfoResponse
    experiments: list[dict[str, Any]] = Field(default_factory=list)
    methods: list[AnalysisMethodSummaryResponse] = Field(default_factory=list)
    records: list[AnalysisExperimentRecordResponse] = Field(default_factory=list)
    matrix_ready: AnalysisMatrixResponse = Field(default_factory=AnalysisMatrixResponse)
    coverage: AnalysisCoverageResponse = Field(default_factory=AnalysisCoverageResponse)
    confidence: AnalysisConfidenceResponse = Field(
        default_factory=AnalysisConfidenceResponse
    )


class AnalysisMethodsFiltersRequest(BaseModel):
    datasets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    main_results_only: bool = False
    include_uncomparable: bool = False


class AnalysisMethodsRequest(BaseModel):
    paper_ids: list[str] = Field(default_factory=list)
    collection_id: str | None = None
    research_question: str | None = None
    filters: AnalysisMethodsFiltersRequest = Field(
        default_factory=AnalysisMethodsFiltersRequest
    )
    refresh_missing: bool = False


class AnalysisMethodsScopeResponse(BaseModel):
    type: str
    paper_ids: list[str] = Field(default_factory=list)
    paper_count: int = 0
    requested_count: int = 0
    collection_id: str | None = None
    default_scope: bool = False


class AnalysisVectorHitResponse(BaseModel):
    paper_id: str
    paper_title: str | None = None
    section_title: str | None = None
    similarity: float = 0.0
    snippet: str = ""


class AnalysisQASupportResponse(BaseModel):
    status: str
    queued: bool = False
    answer: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    latency_ms: int | None = None


class AnalysisMethodsPaperResponse(BaseModel):
    id: str
    title: str
    year: int | None = None
    ingestion_status: str
    has_full_text: bool = False
    source: str
    coverage: AnalysisCoverageResponse = Field(default_factory=AnalysisCoverageResponse)
    confidence: AnalysisConfidenceResponse = Field(
        default_factory=AnalysisConfidenceResponse
    )
    record_count: int = 0
    qa_support: AnalysisQASupportResponse | None = None


class AnalysisMethodsSummaryResponse(BaseModel):
    id: str
    paper_id: str
    paper_title: str
    method_name: str
    source: str
    datasets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    main_result_count: int = 0
    record_count: int = 0
    confidence: float | None = None
    best_metrics: list[str] = Field(default_factory=list)


class AnalysisCrossPaperSummaryResponse(BaseModel):
    answer: str | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    chunks_found: int = 0
    latency_ms: int | None = None


class AnalysisEvidenceResponse(BaseModel):
    scope_hits: list[AnalysisVectorHitResponse] = Field(default_factory=list)
    paper_hits: dict[str, list[AnalysisVectorHitResponse]] = Field(default_factory=dict)


class AnalysisContradictionCandidateResponse(BaseModel):
    dataset: str
    metric: str
    methods: list[str] = Field(default_factory=list)
    reason: str


class AnalysisMethodsCoverageResponse(BaseModel):
    overall: float = 0.0
    papers_total: int = 0
    papers_with_records: int = 0
    papers_with_scope_hits: int = 0
    records_total: int = 0
    records_after_filters: int = 0


class AnalysisMethodsResponse(BaseModel):
    scope: AnalysisMethodsScopeResponse
    research_question: str
    papers: list[AnalysisMethodsPaperResponse] = Field(default_factory=list)
    methods: list[AnalysisMethodsSummaryResponse] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    matrix: AnalysisMatrixResponse = Field(default_factory=AnalysisMatrixResponse)
    filters_applied: AnalysisMethodsFiltersRequest = Field(
        default_factory=AnalysisMethodsFiltersRequest
    )
    cross_paper_summary: AnalysisCrossPaperSummaryResponse | None = None
    evidence: AnalysisEvidenceResponse = Field(default_factory=AnalysisEvidenceResponse)
    contradiction_candidates: list[AnalysisContradictionCandidateResponse] = Field(
        default_factory=list
    )
    coverage: AnalysisMethodsCoverageResponse = Field(
        default_factory=AnalysisMethodsCoverageResponse
    )
    warnings: list[str] = Field(default_factory=list)


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


@router.post(
    "/papers/{paper_id}/extract-experiments",
    response_model=ExperimentExtractionResponse,
)
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


@router.post("/methods", response_model=AnalysisMethodsResponse)
async def analyze_methods(
    body: AnalysisMethodsRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Aggregate methods and results across a paper subset for Evidence Lab.

    Supports explicit paper IDs, collection-scoped analysis, or a default
    recent-paper scope when neither is provided.
    """
    svc = EvidenceLabService(db, user_id=user_id)
    try:
        result = await svc.analyze_methods(
            paper_ids=body.paper_ids or None,
            collection_id=body.collection_id,
            research_question=body.research_question,
            filters=body.filters.model_dump(),
        )
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
