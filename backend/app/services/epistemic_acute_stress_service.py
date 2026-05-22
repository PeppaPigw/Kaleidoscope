"""EpistemicAcuteStressService — Epistemic Acute Stress Detection.

Detects epistemic acute stress — immediate intellectual shock response
within days of a traumatic intellectual event.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ACUTE_STRESS_SYSTEM = """You are an epistemic acute stress specialist. Given immediate intellectual shock, assess acute stress:

Key concepts:
- Epistemic acute stress: immediate shock after intellectual trauma
- Intrusion: unwanted re-experiencing of traumatic event
- Dissociation: numbing or detachment after event
- Avoidance: steering away from reminders
- Arousal: heightened alertness after event
- Time-limited: occurs within days, resolves within month
- Peritraumatic: symptoms during or immediately after event

When epistemic acute stress IS present:
- Immediate shock response
- Unwanted re-experiencing
- Numbing or detachment
- Avoiding reminders
- Heightened alertness
- Within days of event
- During or immediately after

When no acute stress:
- No shock response
- No re-experiencing
- Connected and present
- Not avoiding
- Normal alertness
- No recent trauma
- Stable functioning

Output JSON with: acute_stress_detected (bool), severity (none/mild/moderate/severe), intrusion_type (what re-experiencing), dissociation_level (what detachment), avoidance_pattern (what steering away), arousal_level (what alertness), recommendation (no_acute_stress/mild_supportive_care/significant_brief_therapy/major_intensive_intervention/emergency_severe_dissociation)."""

EPISTEMIC_ACUTE_STRESS_PROMPT = """Detect epistemic acute stress:

Intrusion type: {intrusion_type}
Dissociation level: {dissociation_level}
Avoidance pattern: {avoidance_pattern}
Arousal level: {arousal_level}
Domain: {domain}
Context: {context}

Is there immediate intellectual shock response within days of a traumatic event? Return ONLY valid JSON."""


class EpistemicAcuteStressService:
    """Detects epistemic acute stress — immediate intellectual shock."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intrusion_type: str,
        *,
        dissociation_level: str = "",
        avoidance_pattern: str = "",
        arousal_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic acute stress."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ACUTE_STRESS_PROMPT.format(
                intrusion_type=intrusion_type,
                dissociation_level=dissociation_level or "Not specified",
                avoidance_pattern=avoidance_pattern or "Not specified",
                arousal_level=arousal_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ACUTE_STRESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intrusion_type": intrusion_type[:200],
            "acute_stress_detected": data.get("acute_stress_detected", False),
            "severity": data.get("severity", ""),
            "dissociation_level": data.get("dissociation_level", ""),
            "avoidance_pattern": data.get("avoidance_pattern", ""),
            "arousal_level": data.get("arousal_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
