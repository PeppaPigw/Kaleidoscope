"""EpistemicEmbodimentOverrideService — Epistemic Embodiment Override Detection.

Detects epistemic embodiment override — overriding bodily wisdom with
purely intellectual reasoning when body carries valid information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIMENT_OVERRIDE_SYSTEM = """You are an epistemic embodiment override specialist. Given overriding bodily wisdom with intellect, assess embodiment override:

Key concepts:
- Epistemic embodiment override: overriding bodily wisdom with purely intellectual reasoning
- Intellect over body: privileging intellect over body signals
- Rationalization over sensation: rationalizing away body sensations
- Mind-body hierarchy: imposing hierarchy of mind over body
- Somatic override: overriding somatic information with logic
- Felt sense dismissal: dismissing felt sense in favor of analysis
- Embodied knowledge rejection: rejecting knowledge carried in body

When epistemic embodiment override IS present:
- Body wisdom overridden by intellect
- Intellect privileged over body
- Sensations rationalized away
- Mind imposed over body
- Somatic info overridden
- Felt sense dismissed
- Embodied knowledge rejected

When no embodiment override:
- Body and intellect integrated
- Both valued equally
- Sensations honored
- Mind-body partnership
- Somatic info considered
- Felt sense valued
- Embodied knowledge integrated

Output JSON with: embodiment_override_detected (bool), severity (none/mild/moderate/severe), intellect_over_body (what intellect overriding body about), rationalization_over_sensation (what sensations rationalized away), somatic_override (what somatic info overridden), felt_sense_dismissal (what felt sense dismissed), recommendation (no_embodiment_override/mild_integration_practice/significant_body_honoring/major_intensive_embodiment_restoration/emergency_complete_embodiment_override)."""

EPISTEMIC_EMBODIMENT_OVERRIDE_PROMPT = """Detect epistemic embodiment override:

Intellect over body: {intellect_over_body}
Rationalization over sensation: {rationalization_over_sensation}
Somatic override: {somatic_override}
Felt sense dismissal: {felt_sense_dismissal}
Domain: {domain}
Context: {context}

Is bodily wisdom being overridden with purely intellectual reasoning? Return ONLY valid JSON."""


class EpistemicEmbodimentOverrideService:
    """Detects epistemic embodiment override — overriding body with intellect."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intellect_over_body: str,
        *,
        rationalization_over_sensation: str = "",
        somatic_override: str = "",
        felt_sense_dismissal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodiment override."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIMENT_OVERRIDE_PROMPT.format(
                intellect_over_body=intellect_over_body,
                rationalization_over_sensation=rationalization_over_sensation or "Not specified",
                somatic_override=somatic_override or "Not specified",
                felt_sense_dismissal=felt_sense_dismissal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIMENT_OVERRIDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intellect_over_body": intellect_over_body[:200],
            "embodiment_override_detected": data.get("embodiment_override_detected", False),
            "severity": data.get("severity", ""),
            "rationalization_over_sensation": data.get("rationalization_over_sensation", ""),
            "somatic_override": data.get("somatic_override", ""),
            "felt_sense_dismissal": data.get("felt_sense_dismissal", ""),
            "recommendation": data.get("recommendation", ""),
        }
