"""EpistemicTemporalProjectionService — Epistemic Temporal Projection Detection.

Detects epistemic temporal projection — projecting current conditions
indefinitely into the future without accounting for change.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_PROJECTION_SYSTEM = """You are an epistemic temporal projection specialist. Given projecting current conditions into the future, assess temporal projection:

Key concepts:
- Epistemic temporal projection: projecting current conditions indefinitely into future
- Linear extrapolation: assuming current trends continue linearly
- Stasis assumption: assuming things will stay as they are
- Change blindness future: blind to potential future changes
- Trend permanence: treating current trends as permanent
- Condition fixation: fixated on current conditions as eternal
- Future as present: imagining future as identical to present

When epistemic temporal projection IS present:
- Current conditions projected forward
- Linear extrapolation assumed
- Stasis assumed
- Future change blindness
- Trends treated as permanent
- Conditions fixated as eternal
- Future imagined as present

When no temporal projection:
- Future uncertainty acknowledged
- Nonlinear change considered
- Change expected
- Future change anticipated
- Trends seen as temporary
- Conditions seen as changeable
- Future imagined as different

Output JSON with: temporal_projection_detected (bool), severity (none/mild/moderate/severe), linear_extrapolation (what extrapolated linearly), stasis_assumption (what assumed to stay same), change_blindness_future (what changes not anticipated), trend_permanence (what trends treated as permanent), recommendation (no_temporal_projection/mild_uncertainty_acknowledgment/significant_change_anticipation/major_intensive_future_flexibility/emergency_complete_temporal_projection)."""

EPISTEMIC_TEMPORAL_PROJECTION_PROMPT = """Detect epistemic temporal projection:

Linear extrapolation: {linear_extrapolation}
Stasis assumption: {stasis_assumption}
Change blindness future: {change_blindness_future}
Trend permanence: {trend_permanence}
Domain: {domain}
Context: {context}

Are current conditions being projected indefinitely into the future? Return ONLY valid JSON."""


class EpistemicTemporalProjectionService:
    """Detects epistemic temporal projection — projecting current conditions forward."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        linear_extrapolation: str,
        *,
        stasis_assumption: str = "",
        change_blindness_future: str = "",
        trend_permanence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal projection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_PROJECTION_PROMPT.format(
                linear_extrapolation=linear_extrapolation,
                stasis_assumption=stasis_assumption or "Not specified",
                change_blindness_future=change_blindness_future or "Not specified",
                trend_permanence=trend_permanence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_PROJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "linear_extrapolation": linear_extrapolation[:200],
            "temporal_projection_detected": data.get("temporal_projection_detected", False),
            "severity": data.get("severity", ""),
            "stasis_assumption": data.get("stasis_assumption", ""),
            "change_blindness_future": data.get("change_blindness_future", ""),
            "trend_permanence": data.get("trend_permanence", ""),
            "recommendation": data.get("recommendation", ""),
        }
