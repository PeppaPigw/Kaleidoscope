"""MethodologyRecommenderService — Research Design Advisor.

Recommends optimal scientific methodology for a research question.
Considers domain norms, resource constraints, validity tradeoffs,
and modern best practices (pre-registration, open science, etc.).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RECOMMEND_SYSTEM = """You are a research methodology expert. Given a research question, recommend the optimal methodology considering validity, feasibility, and domain norms.

Output JSON with: recommendation.question, recommendation.recommended_design (name, description, why_optimal), recommendation.alternatives (list of design/pros/cons/when_to_prefer), recommendation.sample_strategy (approach, minimum_n, power_analysis_notes), recommendation.measurement (primary_outcome, secondary_outcomes, instruments), recommendation.analysis_plan (primary_analysis, robustness_checks, pre_registration_elements), recommendation.validity_tradeoffs (list of tradeoff/decision/rationale), recommendation.open_science_checklist (list of practice/priority critical|recommended|optional), recommendation.estimated_timeline, recommendation.common_pitfalls (list of pitfall/how_to_avoid), recommendation.confidence (0-1)."""

RECOMMEND_PROMPT = """Recommend methodology for this research question:

Question: {question}
Domain: {domain}
Constraints: {constraints_text}
Prior work: {prior_text}
Resources available: {resources}

Recommend the optimal research design. Return ONLY valid JSON."""

COMPARE_SYSTEM = """You are a methodology comparison expert. Given two or more research designs for the same question, provide a rigorous comparison across all validity dimensions.

Output JSON with: comparison.question, comparison.designs (list of name/description), comparison.dimensions (list of dimension/scores where scores is dict of design_name to score 0-1/winner/rationale), comparison.overall_winner, comparison.context_dependencies (list of condition/favored_design - when each design becomes optimal), comparison.hybrid_possibility (whether combining designs adds value, how), comparison.verdict."""

COMPARE_PROMPT = """Compare these research designs:

Question: {question}
Designs to compare:
{designs_text}

Domain: {domain}
Constraints: {constraints}

Compare rigorously across all validity dimensions. Return ONLY valid JSON."""


class MethodologyRecommenderService:
    """Recommends optimal research methodology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend(
        self,
        question: str,
        *,
        domain: str = "",
        constraints: list[str] | None = None,
        resources: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Recommend optimal methodology for a research question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        constraints_text = "\n".join(f"- {c}" for c in (constraints or [])) or "None specified"
        prior = await self._gather_prior(question, dossier_id)
        prior_text = "\n".join(f"- {p}" for p in prior[:6]) or "None available"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RECOMMEND_PROMPT.format(
                question=question,
                domain=domain or "general research",
                constraints_text=constraints_text,
                prior_text=prior_text,
                resources=resources or "Standard academic resources",
            ),
            system=RECOMMEND_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        rec = data.get("recommendation", data)

        return {
            "question": question,
            "recommended_design": rec.get("recommended_design", {}),
            "alternatives": rec.get("alternatives", []),
            "sample_strategy": rec.get("sample_strategy", {}),
            "measurement": rec.get("measurement", {}),
            "analysis_plan": rec.get("analysis_plan", {}),
            "validity_tradeoffs": rec.get("validity_tradeoffs", []),
            "open_science_checklist": rec.get("open_science_checklist", []),
            "estimated_timeline": rec.get("estimated_timeline", ""),
            "common_pitfalls": rec.get("common_pitfalls", []),
            "confidence": rec.get("confidence", 0),
        }

    async def compare_designs(
        self,
        question: str,
        designs: list[str],
        *,
        domain: str = "",
        constraints: str = "",
    ) -> dict:
        """Compare multiple research designs for the same question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        designs_text = "\n".join(f"{i+1}. {d}" for i, d in enumerate(designs))

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPARE_PROMPT.format(
                question=question,
                designs_text=designs_text,
                domain=domain or "general",
                constraints=constraints or "None",
            ),
            system=COMPARE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        comp = data.get("comparison", data)

        return {
            "question": question,
            "designs": comp.get("designs", []),
            "dimensions": comp.get("dimensions", []),
            "overall_winner": comp.get("overall_winner", ""),
            "context_dependencies": comp.get("context_dependencies", []),
            "hybrid_possibility": comp.get("hybrid_possibility", ""),
            "verdict": comp.get("verdict", ""),
        }

    async def _gather_prior(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{query[:100]} methodology design", top_k=5)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
