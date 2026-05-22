"""KnowledgeHoardingService — Knowledge Hoarding Detection.

Detects knowledge hoarding — withholding knowledge for strategic
advantage, where information is kept private not for legitimate
reasons but to maintain power, status, or competitive edge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_HOARDING_SYSTEM = """You are a knowledge hoarding specialist. Given a situation, assess whether knowledge is being withheld for strategic advantage:

Key concepts:
- Knowledge hoarding: withholding for strategic advantage
- Information asymmetry exploitation: using info gaps for power
- Strategic opacity: deliberate lack of transparency
- Knowledge as currency: treating knowledge as power
- Gatekeeping for advantage: controlling access for benefit
- Selective sharing: sharing only what serves interests
- Artificial scarcity: making knowledge scarce when it needn't be

When knowledge hoarding IS present:
- Knowledge withheld for strategic advantage
- Information asymmetry deliberately maintained
- Transparency avoided to preserve power
- Knowledge treated as currency for exchange
- Access controlled for personal benefit
- Sharing selective and self-serving
- Artificial scarcity created around knowledge

When knowledge protection is appropriate:
- Legitimate confidentiality requirements
- Privacy protections for individuals
- Security-sensitive information
- Intellectual property with legal protection
- Premature sharing would cause harm
- Information not yet verified
- Sharing would violate trust or agreements

Output JSON with: hoarding_present (bool), severity (none/mild/moderate/severe), situation (what situation is analyzed), knowledge_withheld (what is being hoarded), strategic_advantage (what advantage is gained), legitimate_reason (whether legitimate reasons exist), recommendation (appropriate_knowledge_protection/mild_selective_sharing/significant_knowledge_hoarding/major_strategic_withholding/share_knowledge_appropriately)."""

KNOWLEDGE_HOARDING_PROMPT = """Detect knowledge hoarding:

Situation: {situation}
Knowledge withheld: {withheld}
Reason given: {reason}
Advantage gained: {advantage}
Domain: {domain}
Context: {context}

Is knowledge being withheld for strategic advantage rather than legitimate reasons? Return ONLY valid JSON."""


class KnowledgeHoardingService:
    """Detects knowledge hoarding — withholding knowledge for strategic advantage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        withheld: str = "",
        reason: str = "",
        advantage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge hoarding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_HOARDING_PROMPT.format(
                situation=situation,
                withheld=withheld or "Not specified",
                reason=reason or "Not specified",
                advantage=advantage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_HOARDING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "hoarding_present": data.get("hoarding_present", False),
            "severity": data.get("severity", ""),
            "knowledge_withheld": data.get("knowledge_withheld", ""),
            "strategic_advantage": data.get("strategic_advantage", ""),
            "legitimate_reason": data.get("legitimate_reason", ""),
            "recommendation": data.get("recommendation", ""),
        }
