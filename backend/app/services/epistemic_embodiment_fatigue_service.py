"""EpistemicEmbodimentFatigueService — Epistemic Embodiment Fatigue Detection.

Detects epistemic embodiment fatigue — physical fatigue degrading
epistemic capacity without being noticed or accounted for.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMBODIMENT_FATIGUE_SYSTEM = """You are an epistemic embodiment fatigue specialist. Given physical fatigue degrading epistemic capacity, assess embodiment fatigue:

Key concepts:
- Epistemic embodiment fatigue: physical fatigue degrading epistemic capacity unnoticed
- Unnoticed degradation: capacity degrading without awareness
- Sleep debt effects: sleep debt affecting judgment unrecognized
- Physical exhaustion spillover: physical exhaustion spilling into thinking
- Stamina depletion: intellectual stamina depleted by physical state
- Recovery neglect: neglecting physical recovery needed for thinking
- Body-mind fatigue transfer: fatigue transferring from body to mind

When epistemic embodiment fatigue IS present:
- Physical fatigue degrading capacity
- Degradation unnoticed
- Sleep debt affecting judgment
- Exhaustion spilling into thinking
- Stamina depleted
- Recovery neglected
- Fatigue transferring

When no embodiment fatigue:
- Physical state supporting capacity
- Capacity monitored
- Sleep adequate
- Energy supporting thinking
- Stamina available
- Recovery maintained
- Body supporting mind

Output JSON with: embodiment_fatigue_detected (bool), severity (none/mild/moderate/severe), unnoticed_degradation (what capacity degrading unnoticed), sleep_debt_effects (what sleep debt affecting), exhaustion_spillover (what exhaustion spilling into), recovery_neglect (what recovery neglected), recommendation (no_embodiment_fatigue/mild_rest_awareness/significant_recovery_needed/major_intensive_physical_restoration/emergency_complete_embodiment_fatigue)."""

EPISTEMIC_EMBODIMENT_FATIGUE_PROMPT = """Detect epistemic embodiment fatigue:

Unnoticed degradation: {unnoticed_degradation}
Sleep debt effects: {sleep_debt_effects}
Exhaustion spillover: {exhaustion_spillover}
Recovery neglect: {recovery_neglect}
Domain: {domain}
Context: {context}

Is physical fatigue degrading epistemic capacity unnoticed? Return ONLY valid JSON."""


class EpistemicEmbodimentFatigueService:
    """Detects epistemic embodiment fatigue — physical fatigue degrading capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unnoticed_degradation: str,
        *,
        sleep_debt_effects: str = "",
        exhaustion_spillover: str = "",
        recovery_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic embodiment fatigue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMBODIMENT_FATIGUE_PROMPT.format(
                unnoticed_degradation=unnoticed_degradation,
                sleep_debt_effects=sleep_debt_effects or "Not specified",
                exhaustion_spillover=exhaustion_spillover or "Not specified",
                recovery_neglect=recovery_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMBODIMENT_FATIGUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unnoticed_degradation": unnoticed_degradation[:200],
            "embodiment_fatigue_detected": data.get("embodiment_fatigue_detected", False),
            "severity": data.get("severity", ""),
            "sleep_debt_effects": data.get("sleep_debt_effects", ""),
            "exhaustion_spillover": data.get("exhaustion_spillover", ""),
            "recovery_neglect": data.get("recovery_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
