"""EpistemicIntellectualJealousyService — Epistemic Intellectual Jealousy Detection.

Detects epistemic intellectual jealousy — jealousy over others entering
one's intellectual territory or domain of expertise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_JEALOUSY_SYSTEM = """You are an epistemic intellectual jealousy specialist. Given jealousy over intellectual territory, assess intellectual jealousy:

Key concepts:
- Epistemic intellectual jealousy: jealousy over others in one's domain
- Territory threat: others encroaching on intellectual space
- Expertise possessiveness: treating knowledge domain as owned
- Newcomer hostility: resenting new entrants to field
- Priority anxiety: fear of losing first-mover status
- Domain guarding: actively excluding others from area
- Recognition hoarding: wanting sole credit for domain

When epistemic intellectual jealousy IS present:
- Jealousy over others in domain
- Others encroaching on space
- Treating domain as owned
- Resenting new entrants
- Fear of losing priority
- Excluding others from area
- Wanting sole credit

When no intellectual jealousy:
- Welcoming others to domain
- Open intellectual space
- Sharing knowledge freely
- Welcoming newcomers
- Secure in contributions
- Including others
- Sharing credit

Output JSON with: intellectual_jealousy_detected (bool), severity (none/mild/moderate/severe), territory_threat (what encroaching), expertise_possessiveness (what treating as owned), newcomer_hostility (what resenting), priority_anxiety (what fearing losing), recommendation (no_intellectual_jealousy/mild_openness_practice/significant_sharing_work/major_intensive_generosity_therapy/emergency_active_exclusion)."""

EPISTEMIC_INTELLECTUAL_JEALOUSY_PROMPT = """Detect epistemic intellectual jealousy:

Territory threat: {territory_threat}
Expertise possessiveness: {expertise_possessiveness}
Newcomer hostility: {newcomer_hostility}
Priority anxiety: {priority_anxiety}
Domain: {domain}
Context: {context}

Is there jealousy over others entering one's intellectual territory? Return ONLY valid JSON."""


class EpistemicIntellectualJealousyService:
    """Detects epistemic intellectual jealousy — jealousy over intellectual territory."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        territory_threat: str,
        *,
        expertise_possessiveness: str = "",
        newcomer_hostility: str = "",
        priority_anxiety: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual jealousy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_JEALOUSY_PROMPT.format(
                territory_threat=territory_threat,
                expertise_possessiveness=expertise_possessiveness or "Not specified",
                newcomer_hostility=newcomer_hostility or "Not specified",
                priority_anxiety=priority_anxiety or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_JEALOUSY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "territory_threat": territory_threat[:200],
            "intellectual_jealousy_detected": data.get("intellectual_jealousy_detected", False),
            "severity": data.get("severity", ""),
            "expertise_possessiveness": data.get("expertise_possessiveness", ""),
            "newcomer_hostility": data.get("newcomer_hostility", ""),
            "priority_anxiety": data.get("priority_anxiety", ""),
            "recommendation": data.get("recommendation", ""),
        }
