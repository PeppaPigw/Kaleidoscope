"""EpistemicBeliefMourningService — Epistemic Belief Mourning Detection.

Detects epistemic belief mourning — mourning the loss of cherished
beliefs that once provided meaning and structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BELIEF_MOURNING_SYSTEM = """You are an epistemic belief mourning specialist. Given mourning lost beliefs, assess belief mourning:

Key concepts:
- Epistemic belief mourning: mourning loss of cherished beliefs
- Meaning vacuum: loss of meaning when beliefs die
- Identity disruption: who am I without this belief
- Community loss: losing belonging when beliefs change
- Nostalgia for certainty: missing when things were clear
- Grief stages: denial, anger, bargaining about lost beliefs
- Incomplete mourning: stuck in grief over old beliefs

When epistemic belief mourning IS present:
- Mourning loss of beliefs
- Loss of meaning
- Identity disrupted
- Losing belonging
- Missing certainty
- Grief stages active
- Stuck in grief

When no belief mourning:
- Beliefs evolving naturally
- Meaning maintained
- Identity stable through change
- Belonging maintained
- Comfortable with uncertainty
- Processing complete
- Moving forward

Output JSON with: belief_mourning_detected (bool), severity (none/mild/moderate/severe), meaning_vacuum (what lost meaning from), identity_disruption (what identity disrupted by), community_loss (what belonging lost), nostalgia_for_certainty (what missing), recommendation (no_belief_mourning/mild_grief_acknowledgment/significant_mourning_support/major_intensive_grief_processing/emergency_severe_meaning_crisis)."""

EPISTEMIC_BELIEF_MOURNING_PROMPT = """Detect epistemic belief mourning:

Meaning vacuum: {meaning_vacuum}
Identity disruption: {identity_disruption}
Community loss: {community_loss}
Nostalgia for certainty: {nostalgia_for_certainty}
Domain: {domain}
Context: {context}

Is there mourning the loss of cherished beliefs? Return ONLY valid JSON."""


class EpistemicBeliefMourningService:
    """Detects epistemic belief mourning — mourning loss of cherished beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meaning_vacuum: str,
        *,
        identity_disruption: str = "",
        community_loss: str = "",
        nostalgia_for_certainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic belief mourning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BELIEF_MOURNING_PROMPT.format(
                meaning_vacuum=meaning_vacuum,
                identity_disruption=identity_disruption or "Not specified",
                community_loss=community_loss or "Not specified",
                nostalgia_for_certainty=nostalgia_for_certainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BELIEF_MOURNING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meaning_vacuum": meaning_vacuum[:200],
            "belief_mourning_detected": data.get("belief_mourning_detected", False),
            "severity": data.get("severity", ""),
            "identity_disruption": data.get("identity_disruption", ""),
            "community_loss": data.get("community_loss", ""),
            "nostalgia_for_certainty": data.get("nostalgia_for_certainty", ""),
            "recommendation": data.get("recommendation", ""),
        }
