"""EpistemicComparisonAsymmetryService — Epistemic Comparison Asymmetry Detection.

Detects epistemic comparison asymmetry — comparing things asymmetrically,
applying different standards or scrutiny to each side.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARISON_ASYMMETRY_SYSTEM = """You are an epistemic comparison asymmetry specialist. Given asymmetric comparisons, assess comparison asymmetry:

Key concepts:
- Epistemic comparison asymmetry: applying different standards to each side
- Selective scrutiny: scrutinizing one side more than the other
- Charitable vs uncharitable: charitable interpretation of one, uncharitable of other
- Best vs worst: comparing best of one with worst of other
- Ideal vs real: comparing ideal of one with reality of other
- Cost-benefit asymmetry: counting costs of one but only benefits of other
- Evidence standard asymmetry: different evidence standards for each side

When epistemic comparison asymmetry IS present:
- Different standards applied
- Scrutiny selective
- Charity asymmetric
- Best compared with worst
- Ideal compared with real
- Costs and benefits asymmetric
- Evidence standards different

When no comparison asymmetry:
- Same standards applied
- Scrutiny balanced
- Charity symmetric
- Like compared with like
- Same level compared
- Costs and benefits both counted
- Evidence standards consistent

Output JSON with: comparison_asymmetry_detected (bool), severity (none/mild/moderate/severe), selective_scrutiny (what selective scrutiny), charitable_asymmetry (what charity asymmetric), best_vs_worst (what best-worst comparison), evidence_standard_asymmetry (what evidence asymmetry), recommendation (no_comparison_asymmetry/mild_symmetry_awareness/significant_standard_equalization/major_intensive_comparison_balancing/emergency_complete_comparison_asymmetry)."""

EPISTEMIC_COMPARISON_ASYMMETRY_PROMPT = """Detect epistemic comparison asymmetry:

Selective scrutiny: {selective_scrutiny}
Charitable asymmetry: {charitable_asymmetry}
Best vs worst: {best_vs_worst}
Evidence standard asymmetry: {evidence_standard_asymmetry}
Domain: {domain}
Context: {context}

Are different standards being applied to each side of a comparison? Return ONLY valid JSON."""


class EpistemicComparisonAsymmetryService:
    """Detects epistemic comparison asymmetry — unequal standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        selective_scrutiny: str,
        *,
        charitable_asymmetry: str = "",
        best_vs_worst: str = "",
        evidence_standard_asymmetry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic comparison asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARISON_ASYMMETRY_PROMPT.format(
                selective_scrutiny=selective_scrutiny,
                charitable_asymmetry=charitable_asymmetry or "Not specified",
                best_vs_worst=best_vs_worst or "Not specified",
                evidence_standard_asymmetry=evidence_standard_asymmetry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARISON_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "selective_scrutiny": selective_scrutiny[:200],
            "comparison_asymmetry_detected": data.get("comparison_asymmetry_detected", False),
            "severity": data.get("severity", ""),
            "charitable_asymmetry": data.get("charitable_asymmetry", ""),
            "best_vs_worst": data.get("best_vs_worst", ""),
            "evidence_standard_asymmetry": data.get("evidence_standard_asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
