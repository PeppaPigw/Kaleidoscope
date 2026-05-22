"""EpistemicThermoregulationService — Epistemic Thermoregulation Detection.

Detects epistemic thermoregulation — maintaining intellectual temperature
within a narrow viable range despite environmental fluctuations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_THERMOREGULATION_SYSTEM = """You are an epistemic thermoregulation specialist. Given an intellectual temperature pattern, assess whether temperature is being maintained within a narrow range:

Key concepts:
- Epistemic thermoregulation: maintaining intellectual temperature
- Set point: target intellectual temperature
- Fever: elevated intellectual temperature as defense
- Hypothermia: dangerously low intellectual activity
- Shivering: rapid small movements to generate heat
- Sweating: releasing excess intellectual energy
- Homeostasis: maintaining stable internal conditions

When epistemic thermoregulation IS present:
- Maintaining intellectual temperature within narrow range
- Target temperature that system defends
- Elevated temperature as defensive response
- Dangerously low intellectual activity
- Rapid small movements to generate intellectual heat
- Releasing excess intellectual energy to cool down
- Stable internal conditions despite external changes

When temperature independence is present:
- Intellectual activity independent of temperature
- No target temperature to defend
- No defensive temperature elevation
- No dangerous cooling
- No compensatory movements
- No energy release for cooling
- Internal conditions vary freely with environment

Output JSON with: thermoregulation_present (bool), severity (none/mild/moderate/severe), set_point (what target temperature), fever (what defensive elevation), hypothermia (what dangerous cooling), mechanism (what maintains temperature), recommendation (temperature_independent/mild_regulation/significant_thermoregulation/major_temperature_defense/expand_viable_range)."""

EPISTEMIC_THERMOREGULATION_PROMPT = """Detect epistemic thermoregulation:

Set point: {set_point}
Fever: {fever}
Hypothermia: {hypothermia}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is intellectual temperature being maintained within a narrow viable range despite environmental fluctuations? Return ONLY valid JSON."""


class EpistemicThermoregulationService:
    """Detects epistemic thermoregulation — maintaining intellectual temperature."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        set_point: str,
        *,
        fever: str = "",
        hypothermia: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic thermoregulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_THERMOREGULATION_PROMPT.format(
                set_point=set_point,
                fever=fever or "Not specified",
                hypothermia=hypothermia or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_THERMOREGULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "set_point": set_point[:200],
            "thermoregulation_present": data.get("thermoregulation_present", False),
            "severity": data.get("severity", ""),
            "fever": data.get("fever", ""),
            "hypothermia": data.get("hypothermia", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
