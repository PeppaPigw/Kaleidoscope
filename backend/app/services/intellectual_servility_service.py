"""IntellectualServilityService — Intellectual Servility Detection.

Detects intellectual servility — excessive deference to authority,
tradition, or consensus that prevents independent thinking and
genuine intellectual contribution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INTELLECTUAL_SERVILITY_SYSTEM = """You are an intellectual servility specialist. Given a knowledge interaction, assess whether excessive deference is preventing genuine thinking:

Key concepts:
- Intellectual servility: excessive deference preventing thought
- Authority worship: uncritical acceptance of authority
- Tradition bondage: unable to think beyond tradition
- Consensus slavery: following consensus without understanding
- Intellectual submission: surrendering own judgment entirely
- Deference excess: deferring beyond what's warranted
- Thinking outsourcing: letting others think for you

When intellectual servility IS present:
- Deference to authority prevents independent thought
- Tradition followed without understanding or questioning
- Consensus accepted without personal evaluation
- Own judgment entirely surrendered to others
- Deference exceeds what evidence warrants
- Thinking outsourced to authorities
- No independent intellectual contribution

When appropriate deference exists:
- Deference proportional to demonstrated expertise
- Tradition understood before being followed
- Consensus evaluated before being accepted
- Own judgment exercised within appropriate limits
- Deference based on evidence of reliability
- Others' thinking informs but doesn't replace own
- Independent contribution made within constraints

Output JSON with: servility_present (bool), severity (none/mild/moderate/severe), interaction (what interaction is analyzed), deference (what deference is shown), authority (what authority is deferred to), independence_lost (what independent thought is lost), recommendation (appropriate_deference/mild_over_deference/significant_intellectual_servility/major_thinking_surrender/exercise_independent_judgment)."""

INTELLECTUAL_SERVILITY_PROMPT = """Detect intellectual servility:

Interaction: {interaction}
Authority deferred to: {authority}
Independent thought: {independence}
Basis for deference: {basis}
Domain: {domain}
Context: {context}

Is excessive deference preventing genuine independent thinking? Return ONLY valid JSON."""


class IntellectualServilityService:
    """Detects intellectual servility — excessive deference preventing thought."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        authority: str = "",
        independence: str = "",
        basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect intellectual servility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INTELLECTUAL_SERVILITY_PROMPT.format(
                interaction=interaction,
                authority=authority or "Not specified",
                independence=independence or "Not specified",
                basis=basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INTELLECTUAL_SERVILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "servility_present": data.get("servility_present", False),
            "severity": data.get("severity", ""),
            "deference": data.get("deference", ""),
            "authority": data.get("authority", ""),
            "independence_lost": data.get("independence_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
