"""EpistemicSuperiorityDismissalService — Epistemic Superiority Dismissal Detection.

Detects epistemic superiority dismissal — dismissing others' ideas
from a position of assumed intellectual superiority.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPERIORITY_DISMISSAL_SYSTEM = """You are an epistemic superiority dismissal specialist. Given dismissal from assumed superiority, assess superiority dismissal:

Key concepts:
- Epistemic superiority dismissal: dismissing from assumed superiority
- Authority presumption: assuming right to dismiss without engagement
- Rank-based rejection: rejecting ideas based on perceived hierarchy
- Expertise weaponization: using credentials to shut down discussion
- Dismissive authority: exercising power to end inquiry
- Hierarchical silencing: using position to silence others
- Merit assumption: assuming own ideas inherently better

When epistemic superiority dismissal IS present:
- Dismissing from assumed superiority
- Assuming right to dismiss
- Rejecting based on hierarchy
- Using credentials to shut down
- Exercising power to end inquiry
- Using position to silence
- Assuming own ideas better

When no superiority dismissal:
- Engaging as equals
- Earning dismissal through argument
- Judging ideas not people
- Using credentials to inform
- Encouraging inquiry
- Amplifying others' voices
- Humble about own ideas

Output JSON with: superiority_dismissal_detected (bool), severity (none/mild/moderate/severe), authority_presumption (what assuming right to dismiss), rank_based_rejection (what rejecting by hierarchy), expertise_weaponization (what shutting down with), hierarchical_silencing (what silencing), recommendation (no_superiority_dismissal/mild_equality_practice/significant_humility_work/major_intensive_power_processing/emergency_active_silencing)."""

EPISTEMIC_SUPERIORITY_DISMISSAL_PROMPT = """Detect epistemic superiority dismissal:

Authority presumption: {authority_presumption}
Rank based rejection: {rank_based_rejection}
Expertise weaponization: {expertise_weaponization}
Hierarchical silencing: {hierarchical_silencing}
Domain: {domain}
Context: {context}

Is there dismissing others from a position of assumed superiority? Return ONLY valid JSON."""


class EpistemicSuperiorityDismissalService:
    """Detects epistemic superiority dismissal — dismissing from assumed superiority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        authority_presumption: str,
        *,
        rank_based_rejection: str = "",
        expertise_weaponization: str = "",
        hierarchical_silencing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic superiority dismissal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPERIORITY_DISMISSAL_PROMPT.format(
                authority_presumption=authority_presumption,
                rank_based_rejection=rank_based_rejection or "Not specified",
                expertise_weaponization=expertise_weaponization or "Not specified",
                hierarchical_silencing=hierarchical_silencing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPERIORITY_DISMISSAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "authority_presumption": authority_presumption[:200],
            "superiority_dismissal_detected": data.get("superiority_dismissal_detected", False),
            "severity": data.get("severity", ""),
            "rank_based_rejection": data.get("rank_based_rejection", ""),
            "expertise_weaponization": data.get("expertise_weaponization", ""),
            "hierarchical_silencing": data.get("hierarchical_silencing", ""),
            "recommendation": data.get("recommendation", ""),
        }
