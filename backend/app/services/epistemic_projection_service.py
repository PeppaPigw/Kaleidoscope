"""EpistemicProjectionService — Epistemic Projection Detection.

Detects epistemic projection — attributing one's own intellectual flaws,
biases, or weaknesses to others rather than acknowledging them in oneself.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROJECTION_SYSTEM = """You are an epistemic projection specialist. Given attribution of own flaws to others, assess projection:

Key concepts:
- Epistemic projection: attributing own flaws to others
- Disowning: refusing to acknowledge own intellectual weakness
- Attribution: seeing own bias in others instead
- Shadow: the unacknowledged intellectual self
- Accusation pattern: accusing others of what self does
- Blind spot maintenance: cannot see own flaw
- Externalization: placing internal problem outside

When epistemic projection IS present:
- Attributing own flaws to others
- Refusing to acknowledge weakness
- Seeing own bias in others
- Unacknowledged intellectual self
- Accusing others of own behavior
- Cannot see own flaw
- Placing problem outside

When no projection:
- Owning own flaws
- Acknowledging weakness
- Seeing others accurately
- Self-aware
- Accurate attribution
- Seeing own flaws
- Internal accountability

Output JSON with: projection_detected (bool), severity (none/mild/moderate/severe), disowning_pattern (what refusing), attribution_target (what seeing in others), accusation_pattern (what accusing), blind_spot (what cannot see), recommendation (no_projection/mild_self_reflection/significant_shadow_work/major_intensive_integration/emergency_complete_externalization)."""

EPISTEMIC_PROJECTION_PROMPT = """Detect epistemic projection:

Disowning pattern: {disowning_pattern}
Attribution target: {attribution_target}
Accusation pattern: {accusation_pattern}
Blind spot: {blind_spot}
Domain: {domain}
Context: {context}

Is there attribution of own intellectual flaws or biases to others? Return ONLY valid JSON."""


class EpistemicProjectionService:
    """Detects epistemic projection — attributing own flaws to others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disowning_pattern: str,
        *,
        attribution_target: str = "",
        accusation_pattern: str = "",
        blind_spot: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic projection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROJECTION_PROMPT.format(
                disowning_pattern=disowning_pattern,
                attribution_target=attribution_target or "Not specified",
                accusation_pattern=accusation_pattern or "Not specified",
                blind_spot=blind_spot or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disowning_pattern": disowning_pattern[:200],
            "projection_detected": data.get("projection_detected", False),
            "severity": data.get("severity", ""),
            "attribution_target": data.get("attribution_target", ""),
            "accusation_pattern": data.get("accusation_pattern", ""),
            "blind_spot": data.get("blind_spot", ""),
            "recommendation": data.get("recommendation", ""),
        }
