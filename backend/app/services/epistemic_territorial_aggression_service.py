"""EpistemicTerritorialAggressionService — Epistemic Territorial Aggression Detection.

Detects epistemic territorial aggression — aggressive defense of intellectual
territory against perceived encroachment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TERRITORIAL_AGGRESSION_SYSTEM = """You are an epistemic territorial aggression specialist. Given aggressive intellectual territory defense, assess territorial aggression:

Key concepts:
- Epistemic territorial aggression: aggressive defense of intellectual space
- Boundary enforcement: harsh responses to perceived encroachment
- Gatekeeping violence: using expertise to exclude others
- Intimidation tactics: scaring others away from domain
- Credential weaponization: using qualifications as weapons
- Public humiliation: shaming those who enter territory
- Intellectual bullying: using knowledge to dominate

When epistemic territorial aggression IS present:
- Aggressive defense of space
- Harsh responses to encroachment
- Using expertise to exclude
- Scaring others away
- Using qualifications as weapons
- Shaming those who enter
- Using knowledge to dominate

When no territorial aggression:
- Open intellectual borders
- Welcoming responses
- Using expertise to include
- Encouraging others
- Sharing qualifications
- Supporting newcomers
- Using knowledge to empower

Output JSON with: territorial_aggression_detected (bool), severity (none/mild/moderate/severe), boundary_enforcement (what harsh response), gatekeeping_violence (what excluding), intimidation_tactics (what scaring), credential_weaponization (what weaponizing), recommendation (no_territorial_aggression/mild_openness_practice/significant_inclusion_work/major_intensive_generosity_therapy/emergency_active_bullying)."""

EPISTEMIC_TERRITORIAL_AGGRESSION_PROMPT = """Detect epistemic territorial aggression:

Boundary enforcement: {boundary_enforcement}
Gatekeeping violence: {gatekeeping_violence}
Intimidation tactics: {intimidation_tactics}
Credential weaponization: {credential_weaponization}
Domain: {domain}
Context: {context}

Is there aggressive defense of intellectual territory? Return ONLY valid JSON."""


class EpistemicTerritorialAggressionService:
    """Detects epistemic territorial aggression — aggressive defense of intellectual territory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        boundary_enforcement: str,
        *,
        gatekeeping_violence: str = "",
        intimidation_tactics: str = "",
        credential_weaponization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic territorial aggression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TERRITORIAL_AGGRESSION_PROMPT.format(
                boundary_enforcement=boundary_enforcement,
                gatekeeping_violence=gatekeeping_violence or "Not specified",
                intimidation_tactics=intimidation_tactics or "Not specified",
                credential_weaponization=credential_weaponization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TERRITORIAL_AGGRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "boundary_enforcement": boundary_enforcement[:200],
            "territorial_aggression_detected": data.get("territorial_aggression_detected", False),
            "severity": data.get("severity", ""),
            "gatekeeping_violence": data.get("gatekeeping_violence", ""),
            "intimidation_tactics": data.get("intimidation_tactics", ""),
            "credential_weaponization": data.get("credential_weaponization", ""),
            "recommendation": data.get("recommendation", ""),
        }
