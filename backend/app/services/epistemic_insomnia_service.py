"""EpistemicInsomniaService — Epistemic Insomnia Detection.

Detects epistemic insomnia — inability to stop intellectual activity,
racing thoughts preventing cognitive rest and recovery.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSOMNIA_SYSTEM = """You are an epistemic insomnia specialist. Given inability to stop intellectual activity, assess insomnia patterns:

Key concepts:
- Epistemic insomnia: inability to stop intellectual activity
- Racing thoughts: uncontrollable stream of ideas
- Hyperarousal: intellectual system stuck in overdrive
- Sleep onset: cannot transition from active to rest
- Maintenance: waking up with thoughts mid-rest
- Cognitive fatigue: exhaustion from inability to rest
- Sleep hygiene: practices for intellectual rest

When epistemic insomnia IS present:
- Inability to stop intellectual activity
- Uncontrollable stream of ideas
- System stuck in overdrive
- Cannot transition to rest
- Waking with thoughts mid-rest
- Exhaustion from no rest
- Poor intellectual rest practices

When no insomnia:
- Able to stop when needed
- Controlled thought flow
- Normal arousal levels
- Smooth transitions to rest
- Uninterrupted rest periods
- Adequate recovery
- Good rest practices

Output JSON with: insomnia_detected (bool), severity (none/mild/moderate/severe), racing_thoughts (what uncontrolled stream), hyperarousal_level (what overdrive), rest_onset (what transition difficulty), fatigue_level (what exhaustion), recommendation (no_insomnia/mild_sleep_hygiene/significant_cognitive_techniques/major_structured_intervention/emergency_complete_exhaustion)."""

EPISTEMIC_INSOMNIA_PROMPT = """Detect epistemic insomnia:

Racing thoughts: {racing_thoughts}
Hyperarousal level: {hyperarousal_level}
Rest onset: {rest_onset}
Fatigue level: {fatigue_level}
Domain: {domain}
Context: {context}

Is there inability to stop intellectual activity with racing thoughts preventing rest? Return ONLY valid JSON."""


class EpistemicInsomniaService:
    """Detects epistemic insomnia — inability to stop intellectual activity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        racing_thoughts: str,
        *,
        hyperarousal_level: str = "",
        rest_onset: str = "",
        fatigue_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic insomnia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSOMNIA_PROMPT.format(
                racing_thoughts=racing_thoughts,
                hyperarousal_level=hyperarousal_level or "Not specified",
                rest_onset=rest_onset or "Not specified",
                fatigue_level=fatigue_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSOMNIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "racing_thoughts": racing_thoughts[:200],
            "insomnia_detected": data.get("insomnia_detected", False),
            "severity": data.get("severity", ""),
            "hyperarousal_level": data.get("hyperarousal_level", ""),
            "rest_onset": data.get("rest_onset", ""),
            "fatigue_level": data.get("fatigue_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
