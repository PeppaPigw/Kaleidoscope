"""EpistemicAnemiaService — Epistemic Anemia Detection.

Detects epistemic anemia — insufficient oxygen-carrying capacity in
intellectual circulation, where ideas lack vitality due to depleted carriers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANEMIA_SYSTEM = """You are an epistemic anemia specialist. Given intellectual circulation, assess whether oxygen-carrying capacity is insufficient:

Key concepts:
- Epistemic anemia: insufficient carriers for intellectual vitality
- Iron deficiency: lack of core binding element
- Hemoglobin depletion: reduced capacity per carrier
- Pallor: visible lack of intellectual color/vitality
- Fatigue: inability to sustain intellectual effort
- Compensatory tachycardia: speeding up to compensate for reduced capacity
- Transfusion need: requiring external intellectual substance

When epistemic anemia IS present:
- Insufficient carriers for intellectual vitality
- Lack of core binding elements for ideas
- Reduced capacity per intellectual carrier
- Visible lack of vitality in reasoning
- Inability to sustain intellectual effort
- Compensatory speeding to mask deficiency
- Need for external intellectual substance

When healthy circulation is present:
- Adequate carriers for vitality
- Sufficient core binding elements
- Full capacity per carrier
- Vibrant intellectual color
- Sustained intellectual effort
- Normal pace without compensation
- Self-sufficient intellectual substance

Output JSON with: anemia_present (bool), severity (none/mild/moderate/severe), iron_deficiency (what core lack), hemoglobin_depletion (what reduced capacity), fatigue (what effort failure), compensatory_response (what speeding), recommendation (healthy_circulation/mild_anemia/significant_anemia/major_depletion/transfuse_intellectual_substance)."""

EPISTEMIC_ANEMIA_PROMPT = """Detect epistemic anemia:

Iron deficiency: {iron_deficiency}
Hemoglobin depletion: {hemoglobin_depletion}
Fatigue: {fatigue}
Compensatory response: {compensatory_response}
Domain: {domain}
Context: {context}

Is there insufficient oxygen-carrying capacity in intellectual circulation? Return ONLY valid JSON."""


class EpistemicAnemiaService:
    """Detects epistemic anemia — insufficient intellectual circulation capacity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        iron_deficiency: str,
        *,
        hemoglobin_depletion: str = "",
        fatigue: str = "",
        compensatory_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anemia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANEMIA_PROMPT.format(
                iron_deficiency=iron_deficiency,
                hemoglobin_depletion=hemoglobin_depletion or "Not specified",
                fatigue=fatigue or "Not specified",
                compensatory_response=compensatory_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANEMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "iron_deficiency": iron_deficiency[:200],
            "anemia_present": data.get("anemia_present", False),
            "severity": data.get("severity", ""),
            "hemoglobin_depletion": data.get("hemoglobin_depletion", ""),
            "fatigue": data.get("fatigue", ""),
            "compensatory_response": data.get("compensatory_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
