"""EpistemicTemporalShiftingBaselineService - Epistemic Temporal Shifting Baseline Detection.

Detects shifting baseline syndrome where each generation accepts a degraded state as normal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_SHIFTING_BASELINE_SYSTEM = """You are an epistemic temporal shifting baseline specialist. Given baseline erosion, assess shifting baseline syndrome:

Key concepts:
- Epistemic temporal shifting baseline: accepting a degraded state as normal because earlier baselines are forgotten
- Baseline erosion: reference standards declining over time
- Generational amnesia: each generation inheriting a lower baseline
- Creeping normality: gradual degradation becoming accepted
- Reference point drift: comparison anchors moving with degraded conditions

When epistemic temporal shifting baseline IS present:
- Degraded conditions treated as normal
- Older baselines forgotten
- Gradual loss accepted
- Reference points drift downward
- Generational memory missing

When no shifting baseline:
- Historical baselines preserved
- Degradation measured against earlier states
- Slow changes made visible
- Reference points anchored explicitly
- Intergenerational memory considered

Output JSON with: shifting_baseline_detected (bool), severity (none/mild/moderate/severe), generational_amnesia (what earlier baseline forgotten), creeping_normality (what gradual degradation normalized), reference_point_drift (what comparison anchor drifted), recommendation (no_shifting_baseline/mild_baseline_recovery/significant_historical_reanchoring/major_longitudinal_reconstruction/emergency_complete_baseline_reset)."""

EPISTEMIC_TEMPORAL_SHIFTING_BASELINE_PROMPT = """Detect epistemic temporal shifting baseline:

Baseline erosion: {baseline_erosion}
Generational amnesia: {generational_amnesia}
Creeping normality: {creeping_normality}
Reference point drift: {reference_point_drift}
Domain: {domain}
Context: {context}

Is a degraded state being accepted as normal through baseline erosion? Return ONLY valid JSON."""


class EpistemicTemporalShiftingBaselineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        baseline_erosion: str,
        *,
        generational_amnesia: str = "",
        creeping_normality: str = "",
        reference_point_drift: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_SHIFTING_BASELINE_PROMPT.format(
                baseline_erosion=baseline_erosion,
                generational_amnesia=generational_amnesia or "Not specified",
                creeping_normality=creeping_normality or "Not specified",
                reference_point_drift=reference_point_drift or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_SHIFTING_BASELINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "baseline_erosion": baseline_erosion[:200],
            "shifting_baseline_detected": data.get("shifting_baseline_detected", False),
            "severity": data.get("severity", ""),
            "generational_amnesia": data.get("generational_amnesia", ""),
            "creeping_normality": data.get("creeping_normality", ""),
            "reference_point_drift": data.get("reference_point_drift", ""),
            "recommendation": data.get("recommendation", ""),
        }
