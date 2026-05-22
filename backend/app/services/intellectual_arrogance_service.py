"""IntellectualArroganceService — Intellectual Arrogance Detection.

Detects intellectual arrogance — overestimating one's own
intellectual abilities or the quality of one's beliefs while
dismissing others' contributions and perspectives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_ARROGANCE_SYSTEM = """You are an intellectual arrogance specialist. Given a knowledge interaction, assess whether intellectual arrogance is distorting inquiry:

Key concepts:
- Intellectual arrogance: overestimating own intellectual abilities
- Epistemic hubris: certainty beyond what evidence warrants
- Dismissiveness: rejecting others' contributions without engagement
- Intellectual vanity: prioritizing appearing smart over being right
- Closed-mindedness: refusing to consider alternative views
- Intellectual domination: using intellect to control rather than learn
- Overconfidence in own judgment: trusting self beyond track record

When intellectual arrogance IS present:
- Own abilities overestimated relative to evidence
- Others' contributions dismissed without engagement
- Certainty exceeds what evidence warrants
- Appearing smart prioritized over being right
- Alternative views refused consideration
- Intellect used to dominate not learn
- Self-trust exceeds demonstrated track record

When intellectual confidence is appropriate:
- Confidence proportional to demonstrated ability
- Others' contributions engaged with substantively
- Certainty calibrated to evidence
- Truth prioritized over appearance
- Alternative views considered seriously
- Intellect used to learn and share
- Self-trust based on track record

Output JSON with: arrogance_present (bool), severity (none/mild/moderate/severe), interaction (what interaction is analyzed), overestimation (what is overestimated), dismissal (what is dismissed), effect (what effect on inquiry), recommendation (appropriate_intellectual_confidence/mild_overconfidence/significant_intellectual_arrogance/major_epistemic_hubris/practice_intellectual_humility)."""

INTELLECTUAL_ARROGANCE_PROMPT = """Detect intellectual arrogance:

Interaction: {interaction}
Self-assessment: {self_assessment}
Treatment of others: {treatment}
Openness to challenge: {openness}
Domain: {domain}
Context: {context}

Is intellectual arrogance distorting inquiry through overconfidence and dismissiveness? Return ONLY valid JSON."""


class IntellectualArroganceService:
    """Detects intellectual arrogance — overestimating own abilities while dismissing others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        self_assessment: str = "",
        treatment: str = "",
        openness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual arrogance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_ARROGANCE_PROMPT.format(
                interaction=interaction,
                self_assessment=self_assessment or "Not specified",
                treatment=treatment or "Not specified",
                openness=openness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_ARROGANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "arrogance_present": data.get("arrogance_present", False),
            "severity": data.get("severity", ""),
            "overestimation": data.get("overestimation", ""),
            "dismissal": data.get("dismissal", ""),
            "effect": data.get("effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
