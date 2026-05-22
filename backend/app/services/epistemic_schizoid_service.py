"""EpistemicSchizoidService — Epistemic Schizoid Detection.

Detects epistemic schizoid — detachment from intellectual relationships
with restricted range of intellectual expression.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCHIZOID_SYSTEM = """You are an epistemic schizoid specialist. Given intellectual detachment, assess schizoid patterns:

Key concepts:
- Epistemic schizoid: detachment from intellectual relationships
- Emotional coldness: flat affect toward intellectual matters
- Solitary preference: choosing to work alone exclusively
- Restricted expression: limited intellectual emotional range
- Indifference: no desire for intellectual closeness
- Anhedonia: little pleasure from intellectual activities
- Fantasy retreat: rich inner intellectual world replacing engagement

When epistemic schizoid IS present:
- Detachment from intellectual relationships
- Flat affect toward intellectual matters
- Choosing to work alone exclusively
- Limited intellectual emotional range
- No desire for intellectual closeness
- Little pleasure from activities
- Rich inner world replacing engagement

When no schizoid:
- Connected intellectual relationships
- Appropriate emotional engagement
- Balance of solo and collaborative work
- Full intellectual emotional range
- Desire for intellectual connection
- Pleasure from activities
- Engaged with external world

Output JSON with: schizoid_detected (bool), severity (none/mild/moderate/severe), detachment_level (what disconnection), emotional_range (what expression), solitary_preference (what isolation choice), fantasy_engagement (what inner world), recommendation (no_schizoid/mild_social_skills/significant_relationship_therapy/major_intensive_engagement/emergency_complete_isolation)."""

EPISTEMIC_SCHIZOID_PROMPT = """Detect epistemic schizoid:

Detachment level: {detachment_level}
Emotional range: {emotional_range}
Solitary preference: {solitary_preference}
Fantasy engagement: {fantasy_engagement}
Domain: {domain}
Context: {context}

Is there detachment from intellectual relationships with restricted expression? Return ONLY valid JSON."""


class EpistemicSchizoidService:
    """Detects epistemic schizoid — detachment from intellectual relationships."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        detachment_level: str,
        *,
        emotional_range: str = "",
        solitary_preference: str = "",
        fantasy_engagement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic schizoid."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCHIZOID_PROMPT.format(
                detachment_level=detachment_level,
                emotional_range=emotional_range or "Not specified",
                solitary_preference=solitary_preference or "Not specified",
                fantasy_engagement=fantasy_engagement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCHIZOID_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "detachment_level": detachment_level[:200],
            "schizoid_detected": data.get("schizoid_detected", False),
            "severity": data.get("severity", ""),
            "emotional_range": data.get("emotional_range", ""),
            "solitary_preference": data.get("solitary_preference", ""),
            "fantasy_engagement": data.get("fantasy_engagement", ""),
            "recommendation": data.get("recommendation", ""),
        }
