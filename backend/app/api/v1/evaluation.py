"""Observability and evaluation API endpoints."""
# mypy: disable-error-code="misc,untyped-decorator"

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.ragflow.evaluation import (
    GroundingChecker,
    LatencyCostTracker,
    RetrievalBenchmark,
)

router = APIRouter(prefix="/ragflow/eval", tags=["ragflow-eval"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]

# Singleton tracker for the process lifetime
_tracker = LatencyCostTracker()


def get_tracker() -> LatencyCostTracker:
    """Return the global latency/cost tracker."""
    return _tracker


class GroundingRequest(BaseModel):
    """Request body for grounding check."""

    answer: str = Field(..., min_length=1)
    sources: list[dict[str, Any]] = Field(default_factory=list)


class MetricRecord(BaseModel):
    """Record a single operation metric."""

    operation: str
    latency_ms: float
    tokens_used: int = 0
    route: str = ""


@router.post("/grounding-check")
async def check_grounding(body: GroundingRequest, _user_id: UserId) -> dict[str, Any]:
    """Check how well an answer is grounded in its sources."""
    return GroundingChecker.check_grounding(body.answer, body.sources)


@router.post("/record-metric")
async def record_metric(body: MetricRecord, _user_id: UserId) -> dict[str, str]:
    """Record an operation metric for observability."""
    _tracker.record(
        operation=body.operation,
        latency_ms=body.latency_ms,
        tokens_used=body.tokens_used,
        route=body.route,
    )
    return {"status": "recorded"}


@router.get("/metrics/summary")
async def metrics_summary(_user_id: UserId) -> dict[str, Any]:
    """Get latency/cost dashboard summary."""
    return _tracker.summary()


@router.get("/benchmark/status")
async def benchmark_status(_user_id: UserId) -> dict[str, Any]:
    """Check if the gold benchmark corpus is available."""
    bench = RetrievalBenchmark()
    corpus = bench.load_corpus()
    return {
        "corpus_available": len(corpus) > 0,
        "question_count": len(corpus),
        "categories": list(
            {item.get("category", "unknown") for item in corpus}
        ),
    }


@router.post("/benchmark/run")
async def run_benchmark(
    db: DbSession,
    _user_id: UserId,
    top_k: int = 10,
    category: str | None = None,
) -> dict[str, Any]:
    """Run retrieval benchmark against the gold corpus."""
    from app.services.ragflow.ragflow_query_service import (
        RagflowQueryService,
    )

    bench = RetrievalBenchmark()
    corpus = bench.load_corpus()
    if not corpus:
        return {"error": "No benchmark corpus available"}

    if category:
        filtered = [q for q in corpus if q.get("category") == category]
        if not filtered:
            return {"error": f"No questions for category '{category}'"}
        bench._corpus = filtered

    service = RagflowQueryService(db)

    async def retriever_fn(
        question: str, top_k: int = 10,
    ) -> list[dict[str, Any]]:
        result = await service.scoped_retrieve(
            question=question, top_k=top_k,
        )
        return result.get("chunks", [])

    return await bench.evaluate_retrieval(retriever_fn, top_k=top_k)


@router.post("/benchmark/compare")
async def run_comparison(db: DbSession, _user_id: UserId) -> dict[str, Any]:
    """Run 4-path comparison for retrieval quality."""
    from app.services.ragflow.evidence_expansion import (
        EvidenceExpansionService,
    )
    from app.services.ragflow.query_router import QueryRouter
    from app.services.ragflow.ragflow_query_service import (
        RagflowQueryService,
    )

    bench = RetrievalBenchmark()
    corpus = bench.load_corpus()
    if not corpus:
        return {"error": "No benchmark corpus available"}

    comparisons: dict[str, Any] = {}
    query_svc = RagflowQueryService(db)
    expansion_svc = EvidenceExpansionService(db)
    router_svc = QueryRouter(db)

    # Path 1: RAGFlow only
    async def ragflow_fn(q: str, top_k: int = 10) -> list:
        r = await query_svc.scoped_retrieve(question=q, top_k=top_k)
        return r.get("chunks", [])

    bench_copy1 = RetrievalBenchmark()
    bench_copy1._corpus = corpus.copy()
    comparisons["ragflow_only"] = await bench_copy1.evaluate_retrieval(
        ragflow_fn, top_k=10,
    )

    # Path 2: RAGFlow + Graph Expansion
    async def expanded_fn(q: str, top_k: int = 10) -> list:
        r = await expansion_svc.get_evidence_pack(query=q, top_k=top_k)
        return r.get("chunks", [])

    bench_copy2 = RetrievalBenchmark()
    bench_copy2._corpus = corpus.copy()
    comparisons["ragflow_graph"] = await bench_copy2.evaluate_retrieval(
        expanded_fn, top_k=10,
    )

    # Path 3: Smart Router (combined)
    async def routed_fn(q: str, top_k: int = 10) -> list:
        r = await router_svc.route(q, top_k=top_k)
        return r.get("hits", r.get("sources", []))

    bench_copy3 = RetrievalBenchmark()
    bench_copy3._corpus = corpus.copy()
    comparisons["smart_router"] = await bench_copy3.evaluate_retrieval(
        routed_fn, top_k=10,
    )

    return {
        "question_count": len(corpus),
        "paths": comparisons,
    }


@router.post("/metrics/reset")
async def reset_metrics(_user_id: UserId) -> dict[str, str]:
    """Reset all accumulated metrics."""
    _tracker._metrics.clear()
    return {"status": "cleared"}

