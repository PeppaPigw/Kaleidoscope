"""EpistemicHemophiliaService — Epistemic Hemophilia Detection.

Detects epistemic hemophilia — inability to form intellectual clots when needed,
where ideas bleed freely from any wound without natural stopping mechanism.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HEMOPHILIA_SYSTEM = """You are an epistemic hemophilia specialist. Given intellectual wound responses, assess whether clotting ability is impaired:

Key concepts:
- Epistemic hemophilia: inability to form intellectual clots when needed
- Factor deficiency: missing clotting component
- Prolonged bleeding: wounds that won't stop
- Spontaneous hemorrhage: bleeding without apparent cause
- Joint damage: accumulated damage from repeated bleeds
- Prophylaxis: preventive factor replacement
- Inhibitor: antibody blocking clotting factor

When epistemic hemophilia IS present:
- Inability to form intellectual clots when needed
- Missing critical clotting components
- Intellectual wounds that won't stop bleeding
- Spontaneous idea loss without apparent cause
- Accumulated damage from repeated intellectual bleeds
- Need for preventive intellectual factor replacement
- Antibodies blocking natural intellectual clotting

When healthy clotting is present:
- Normal intellectual clot formation
- All clotting components present
- Wounds seal appropriately
- No spontaneous bleeding
- No accumulated damage
- No prophylaxis needed
- No inhibitors present

Output JSON with: hemophilia_present (bool), severity (none/mild/moderate/severe), factor_deficiency (what missing component), prolonged_bleeding (what won't stop), spontaneous_hemorrhage (what unprovoked loss), joint_damage (what accumulated harm), recommendation (healthy_clotting/mild_hemophilia/significant_hemophilia/major_clotting_failure/replace_intellectual_clotting_factors)."""

EPISTEMIC_HEMOPHILIA_PROMPT = """Detect epistemic hemophilia:

Factor deficiency: {factor_deficiency}
Prolonged bleeding: {prolonged_bleeding}
Spontaneous hemorrhage: {spontaneous_hemorrhage}
Joint damage: {joint_damage}
Domain: {domain}
Context: {context}

Is there inability to form intellectual clots when needed, with ideas bleeding freely? Return ONLY valid JSON."""


class EpistemicHemophiliaService:
    """Detects epistemic hemophilia — inability to form intellectual clots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        factor_deficiency: str,
        *,
        prolonged_bleeding: str = "",
        spontaneous_hemorrhage: str = "",
        joint_damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hemophilia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HEMOPHILIA_PROMPT.format(
                factor_deficiency=factor_deficiency,
                prolonged_bleeding=prolonged_bleeding or "Not specified",
                spontaneous_hemorrhage=spontaneous_hemorrhage or "Not specified",
                joint_damage=joint_damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HEMOPHILIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "factor_deficiency": factor_deficiency[:200],
            "hemophilia_present": data.get("hemophilia_present", False),
            "severity": data.get("severity", ""),
            "prolonged_bleeding": data.get("prolonged_bleeding", ""),
            "spontaneous_hemorrhage": data.get("spontaneous_hemorrhage", ""),
            "joint_damage": data.get("joint_damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
