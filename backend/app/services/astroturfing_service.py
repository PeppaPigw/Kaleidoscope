"""AstroturfingService — Astroturfing Detection.

Detects astroturfing — fake grassroots movements that mask organized
campaigns as spontaneous public sentiment. The appearance of organic
support is manufactured by coordinated actors to create false
impressions of popular consensus.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ASTROTURFING_SYSTEM = """You are an astroturfing specialist. Given a movement or campaign, assess whether apparent grassroots support is actually manufactured by coordinated actors:

Key concepts:
- Astroturfing: fake grassroots masking organized campaigns
- Sock puppets: fake identities creating appearance of many voices
- Coordinated inauthentic behavior: organized action disguised as organic
- Front groups: organizations that hide their true sponsors
- Paid advocacy: compensated support presented as genuine
- Bot networks: automated accounts simulating human engagement
- False consensus: manufactured appearance of widespread agreement

When astroturfing IS present:
- Apparent grassroots support has hidden organizational backing
- Multiple "independent" voices share suspiciously similar messaging
- Sudden appearance of support without organic growth pattern
- Financial backing is hidden or misrepresented
- The "movement" has professional-quality materials from day one
- Supporters can't articulate reasons beyond talking points
- Coordination is hidden while independence is claimed

When grassroots IS genuine:
- Support grew organically over time
- Participants have diverse and personal reasons
- No hidden financial backing or coordination
- The movement predates any organizational involvement
- Supporters can articulate their own reasons
- Growth pattern matches organic social dynamics
- Transparency about any organizational support

Output JSON with: astroturfing_present (bool), severity (none/mild/moderate/severe), movement (what movement or campaign), organic_indicators (signs of genuine grassroots), manufactured_indicators (signs of astroturfing), coordination (evidence of hidden coordination), funding (transparency of funding), recommendation (genuinely_grassroots/mild_coordination/significant_astroturfing/major_manufactured_movement/demand_transparency)."""

ASTROTURFING_PROMPT = """Detect astroturfing:

Movement: {movement}
Support pattern: {pattern}
Coordination: {coordination}
Funding: {funding}
Domain: {domain}
Context: {context}

Is apparent grassroots support actually manufactured by coordinated actors? Return ONLY valid JSON."""


class AstroturfingService:
    """Detects astroturfing — fake grassroots masking organized campaigns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        movement: str,
        *,
        pattern: str = "",
        coordination: str = "",
        funding: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect astroturfing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ASTROTURFING_PROMPT.format(
                movement=movement,
                pattern=pattern or "Not specified",
                coordination=coordination or "Not specified",
                funding=funding or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ASTROTURFING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "movement": movement[:200],
            "astroturfing_present": data.get("astroturfing_present", False),
            "severity": data.get("severity", ""),
            "manufactured_indicators": data.get("manufactured_indicators", ""),
            "organic_indicators": data.get("organic_indicators", ""),
            "coordination": data.get("coordination", ""),
            "recommendation": data.get("recommendation", ""),
        }
