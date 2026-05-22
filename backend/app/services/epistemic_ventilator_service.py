"""EpistemicVentilatorService — Epistemic Ventilator Dependence Detection.

Detects epistemic ventilator dependence — intellectual systems that cannot
breathe independently and require continuous mechanical support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VENTILATOR_SYSTEM = """You are an epistemic ventilator specialist. Given intellectual systems unable to breathe independently, assess ventilator dependence:

Key concepts:
- Epistemic ventilator: mechanical support for intellectual breathing
- Weaning failure: inability to transition off support
- Barotrauma: damage from excessive pressure support
- PEEP: positive end-expiratory pressure maintaining openness
- Tidal volume: amount of intellectual input per breath
- FiO2: fraction of inspired intellectual oxygen
- Ventilator-associated pneumonia: infection from prolonged support

When epistemic ventilator dependence IS present:
- Cannot breathe intellectually without support
- Failed weaning attempts
- Damage from excessive support pressure
- Requires constant positive pressure
- Inadequate independent tidal volume
- Needs high fraction of supported input
- Infection from prolonged dependence

When no ventilator dependence:
- Independent intellectual breathing
- Successful self-sustaining function
- No pressure damage
- Self-maintaining openness
- Adequate independent volume
- Normal unsupported function
- No dependence complications

Output JSON with: ventilator_dependence (bool), severity (none/mild/moderate/severe), weaning_status (what independence progress), barotrauma_risk (what pressure damage), peep_requirement (what support level), dependence_duration (what time on support), recommendation (no_ventilator_needed/mild_support/significant_ventilation/major_full_ventilator/emergency_cannot_wean)."""

EPISTEMIC_VENTILATOR_PROMPT = """Detect epistemic ventilator dependence:

Weaning status: {weaning_status}
Barotrauma risk: {barotrauma_risk}
PEEP requirement: {peep_requirement}
Dependence duration: {dependence_duration}
Domain: {domain}
Context: {context}

Is the intellectual system unable to breathe independently? Return ONLY valid JSON."""


class EpistemicVentilatorService:
    """Detects epistemic ventilator dependence — systems needing mechanical breathing support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        weaning_status: str,
        *,
        barotrauma_risk: str = "",
        peep_requirement: str = "",
        dependence_duration: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ventilator dependence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VENTILATOR_PROMPT.format(
                weaning_status=weaning_status,
                barotrauma_risk=barotrauma_risk or "Not specified",
                peep_requirement=peep_requirement or "Not specified",
                dependence_duration=dependence_duration or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VENTILATOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "weaning_status": weaning_status[:200],
            "ventilator_dependence": data.get("ventilator_dependence", False),
            "severity": data.get("severity", ""),
            "barotrauma_risk": data.get("barotrauma_risk", ""),
            "peep_requirement": data.get("peep_requirement", ""),
            "dependence_duration": data.get("dependence_duration", ""),
            "recommendation": data.get("recommendation", ""),
        }
