"""EpistemicTemporalAnchoringService — Epistemic Temporal Anchoring Detection.

Detects epistemic temporal anchoring — anchoring to a specific time period
and judging everything by that era's standards or conditions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_ANCHORING_SYSTEM = """You are an epistemic temporal anchoring specialist. Given anchoring to a specific time period, assess temporal anchoring:

Key concepts:
- Epistemic temporal anchoring: anchoring to a specific time period and judging by it
- Era fixation: fixated on a specific era as reference point
- Golden age thinking: treating a past period as the golden standard
- Baseline bias: using a specific time as baseline for all comparison
- Period idealization: idealizing a specific period
- Temporal reference lock: locked to a temporal reference point
- Historical standard imposition: imposing one era's standards on another

When epistemic temporal anchoring IS present:
- Anchored to specific time period
- Era fixated on
- Golden age invoked
- Baseline biased to specific time
- Period idealized
- Temporal reference locked
- Historical standards imposed

When no temporal anchoring:
- Multiple time periods considered
- No era fixation
- No golden age invoked
- Baseline appropriate
- Periods assessed fairly
- Temporal reference flexible
- Standards contextual

Output JSON with: temporal_anchoring_detected (bool), severity (none/mild/moderate/severe), era_fixation (what era fixated on), golden_age_thinking (what golden age invoked), baseline_bias (what baseline biased to), period_idealization (what period idealized), recommendation (no_temporal_anchoring/mild_temporal_flexibility/significant_multi_era_perspective/major_intensive_temporal_deanchoring/emergency_complete_temporal_anchoring)."""

EPISTEMIC_TEMPORAL_ANCHORING_PROMPT = """Detect epistemic temporal anchoring:

Era fixation: {era_fixation}
Golden age thinking: {golden_age_thinking}
Baseline bias: {baseline_bias}
Period idealization: {period_idealization}
Domain: {domain}
Context: {context}

Is there anchoring to a specific time period and judging everything by it? Return ONLY valid JSON."""


class EpistemicTemporalAnchoringService:
    """Detects epistemic temporal anchoring — anchoring to specific time period."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        era_fixation: str,
        *,
        golden_age_thinking: str = "",
        baseline_bias: str = "",
        period_idealization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal anchoring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_ANCHORING_PROMPT.format(
                era_fixation=era_fixation,
                golden_age_thinking=golden_age_thinking or "Not specified",
                baseline_bias=baseline_bias or "Not specified",
                period_idealization=period_idealization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_ANCHORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "era_fixation": era_fixation[:200],
            "temporal_anchoring_detected": data.get("temporal_anchoring_detected", False),
            "severity": data.get("severity", ""),
            "golden_age_thinking": data.get("golden_age_thinking", ""),
            "baseline_bias": data.get("baseline_bias", ""),
            "period_idealization": data.get("period_idealization", ""),
            "recommendation": data.get("recommendation", ""),
        }
