"""EpistemicAdjustmentService — Epistemic Adjustment Disorder Detection.

Detects epistemic adjustment disorder — difficulty adapting to intellectual
change with disproportionate distress or functional impairment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ADJUSTMENT_SYSTEM = """You are an epistemic adjustment disorder specialist. Given difficulty adapting to intellectual change, assess adjustment:

Key concepts:
- Epistemic adjustment: difficulty adapting to intellectual change
- Stressor identified: specific intellectual change triggering distress
- Disproportionate: distress exceeds what change warrants
- Functional impairment: change affecting intellectual performance
- Time-bound: develops within months of stressor
- Subthreshold: doesn't meet criteria for other disorders
- Recovery expected: should resolve once adaptation occurs

When epistemic adjustment IS present:
- Difficulty adapting to change
- Specific change triggering distress
- Distress exceeds what warranted
- Affecting performance
- Within months of stressor
- Below other disorder thresholds
- Expected to resolve

When no adjustment disorder:
- Adapting to change
- Proportionate response
- Distress matches situation
- Performance maintained
- Normal adaptation timeline
- No disorder features
- Already resolved

Output JSON with: adjustment_detected (bool), severity (none/mild/moderate/severe), stressor_type (what change), distress_level (what disproportionate response), functional_impact (what impairment), adaptation_progress (what recovery), recommendation (no_adjustment/mild_supportive_counseling/significant_brief_therapy/major_intensive_support/emergency_severe_impairment)."""

EPISTEMIC_ADJUSTMENT_PROMPT = """Detect epistemic adjustment disorder:

Stressor type: {stressor_type}
Distress level: {distress_level}
Functional impact: {functional_impact}
Adaptation progress: {adaptation_progress}
Domain: {domain}
Context: {context}

Is there difficulty adapting to intellectual change with disproportionate distress? Return ONLY valid JSON."""


class EpistemicAdjustmentService:
    """Detects epistemic adjustment — difficulty adapting to intellectual change."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stressor_type: str,
        *,
        distress_level: str = "",
        functional_impact: str = "",
        adaptation_progress: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic adjustment disorder."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ADJUSTMENT_PROMPT.format(
                stressor_type=stressor_type,
                distress_level=distress_level or "Not specified",
                functional_impact=functional_impact or "Not specified",
                adaptation_progress=adaptation_progress or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ADJUSTMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stressor_type": stressor_type[:200],
            "adjustment_detected": data.get("adjustment_detected", False),
            "severity": data.get("severity", ""),
            "distress_level": data.get("distress_level", ""),
            "functional_impact": data.get("functional_impact", ""),
            "adaptation_progress": data.get("adaptation_progress", ""),
            "recommendation": data.get("recommendation", ""),
        }
