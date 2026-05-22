"""EpistemicEusocialityService — Epistemic Eusociality Detection.

Detects epistemic eusociality — intellectual communities with extreme
division of labor where most members sacrifice individual thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EUSOCIALITY_SYSTEM = """You are an epistemic eusociality specialist. Given an intellectual community, assess whether extreme division of labor sacrifices individual thinking:

Key concepts:
- Epistemic eusociality: extreme division of intellectual labor
- Queen/worker division: few think originally, most execute
- Reproductive division: only some produce new ideas
- Worker sterility: most members unable to produce original thought
- Colony benefit: division benefits the collective at individual cost
- Caste system: rigid intellectual roles assigned to members
- Altruistic sacrifice: individuals sacrificing thinking for colony

When epistemic eusociality IS present:
- Extreme division of intellectual labor in community
- Few members thinking originally while most execute
- Only some members producing new ideas
- Most members unable or not permitted to think originally
- Division benefiting collective at individual cost
- Rigid intellectual roles assigned to community members
- Individuals sacrificing independent thinking for group

When intellectual equality is present:
- Balanced intellectual labor across community
- All members thinking originally
- All members capable of producing new ideas
- No restrictions on original thought
- Individual and collective interests aligned
- Flexible intellectual roles
- Independent thinking encouraged alongside collaboration

Output JSON with: eusociality_present (bool), severity (none/mild/moderate/severe), community (what community shows eusociality), division (what division of labor exists), sacrifice (what individual thinking is sacrificed), colony_benefit (what collective benefit results), recommendation (intellectual_equality/mild_specialization/significant_eusociality/major_caste_system/restore_individual_thinking)."""

EPISTEMIC_EUSOCIALITY_PROMPT = """Detect epistemic eusociality:

Community: {community}
Division: {division}
Sacrifice: {sacrifice}
Colony benefit: {colony_benefit}
Domain: {domain}
Context: {context}

Does this intellectual community show extreme division of labor sacrificing individual thinking? Return ONLY valid JSON."""


class EpistemicEusocialityService:
    """Detects epistemic eusociality — extreme intellectual division of labor."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        community: str,
        *,
        division: str = "",
        sacrifice: str = "",
        colony_benefit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic eusociality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EUSOCIALITY_PROMPT.format(
                community=community,
                division=division or "Not specified",
                sacrifice=sacrifice or "Not specified",
                colony_benefit=colony_benefit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EUSOCIALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "community": community[:200],
            "eusociality_present": data.get("eusociality_present", False),
            "severity": data.get("severity", ""),
            "division": data.get("division", ""),
            "sacrifice": data.get("sacrifice", ""),
            "colony_benefit": data.get("colony_benefit", ""),
            "recommendation": data.get("recommendation", ""),
        }
