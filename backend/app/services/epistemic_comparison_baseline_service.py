"""EpistemicComparisonBaselineService — Epistemic Comparison Baseline Detection.

Detects epistemic comparison baseline failure — comparing without appropriate
baseline or reference point, making comparisons meaningless.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPARISON_BASELINE_SYSTEM = """You are an epistemic comparison baseline specialist. Given comparisons without baselines, assess baseline failure:

Key concepts:
- Epistemic comparison baseline: comparing without appropriate reference point
- Missing counterfactual: no counterfactual baseline for comparison
- Arbitrary reference: arbitrary choice of reference point
- Shifting baseline: baseline shifting over time unnoticed
- Inappropriate baseline: baseline inappropriate for comparison
- Absolute without relative: absolute numbers without relative context
- Before-after without control: before-after comparison without control group

When epistemic comparison baseline failure IS present:
- No appropriate baseline
- Counterfactual missing
- Reference arbitrary
- Baseline shifting
- Baseline inappropriate
- Absolute without relative
- No control comparison

When no baseline failure:
- Appropriate baseline used
- Counterfactual considered
- Reference justified
- Baseline stable or tracked
- Baseline appropriate
- Relative context provided
- Control comparison included

Output JSON with: comparison_baseline_failure_detected (bool), severity (none/mild/moderate/severe), missing_counterfactual (what counterfactual missing), arbitrary_reference (what reference arbitrary), shifting_baseline (what baseline shifting), inappropriate_baseline (what baseline inappropriate), recommendation (no_baseline_failure/mild_baseline_awareness/significant_reference_establishment/major_intensive_baseline_correction/emergency_complete_baseline_failure)."""

EPISTEMIC_COMPARISON_BASELINE_PROMPT = """Detect epistemic comparison baseline failure:

Missing counterfactual: {missing_counterfactual}
Arbitrary reference: {arbitrary_reference}
Shifting baseline: {shifting_baseline}
Inappropriate baseline: {inappropriate_baseline}
Domain: {domain}
Context: {context}

Are comparisons being made without appropriate baseline or reference point? Return ONLY valid JSON."""


class EpistemicComparisonBaselineService:
    """Detects epistemic comparison baseline failure — no reference point."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        missing_counterfactual: str,
        *,
        arbitrary_reference: str = "",
        shifting_baseline: str = "",
        inappropriate_baseline: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic comparison baseline failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPARISON_BASELINE_PROMPT.format(
                missing_counterfactual=missing_counterfactual,
                arbitrary_reference=arbitrary_reference or "Not specified",
                shifting_baseline=shifting_baseline or "Not specified",
                inappropriate_baseline=inappropriate_baseline or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPARISON_BASELINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "missing_counterfactual": missing_counterfactual[:200],
            "comparison_baseline_failure_detected": data.get("comparison_baseline_failure_detected", False),
            "severity": data.get("severity", ""),
            "arbitrary_reference": data.get("arbitrary_reference", ""),
            "shifting_baseline": data.get("shifting_baseline", ""),
            "inappropriate_baseline": data.get("inappropriate_baseline", ""),
            "recommendation": data.get("recommendation", ""),
        }
