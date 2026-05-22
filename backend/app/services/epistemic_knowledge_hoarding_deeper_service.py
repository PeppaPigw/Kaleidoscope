"""EpistemicKnowledgeHoardingDeeperService — Epistemic Knowledge Hoarding Deeper Detection.

Detects deeper epistemic knowledge hoarding — hoarding knowledge as power
rather than sharing it for collective benefit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KNOWLEDGE_HOARDING_DEEPER_SYSTEM = """You are an epistemic knowledge hoarding specialist. Given hoarding knowledge as power, assess deeper knowledge hoarding:

Key concepts:
- Epistemic knowledge hoarding deeper: hoarding knowledge as power
- Information monopoly: maintaining monopoly on information
- Strategic withholding: withholding knowledge for strategic advantage
- Knowledge as currency: treating knowledge as currency for power
- Sharing resistance: resisting sharing knowledge with others
- Expertise protectionism: protecting expertise from being learned by others
- Intellectual scarcity creation: creating artificial scarcity of knowledge

When epistemic knowledge hoarding deeper IS present:
- Hoarding knowledge as power
- Maintaining information monopoly
- Withholding for strategic advantage
- Treating knowledge as currency
- Resisting sharing
- Protecting expertise from others
- Creating artificial scarcity

When no deeper knowledge hoarding:
- Sharing knowledge freely
- Open information
- Sharing without strategic calculation
- Knowledge as commons
- Generous sharing
- Teaching expertise
- Knowledge abundance

Output JSON with: knowledge_hoarding_deeper_detected (bool), severity (none/mild/moderate/severe), information_monopoly (what monopoly maintained on), strategic_withholding (what withheld for advantage), knowledge_as_currency (what treated as currency), sharing_resistance (what resisting sharing), recommendation (no_knowledge_hoarding/mild_sharing_practice/significant_openness_building/major_intensive_generosity/emergency_complete_knowledge_hoarding)."""

EPISTEMIC_KNOWLEDGE_HOARDING_DEEPER_PROMPT = """Detect deeper epistemic knowledge hoarding:

Information monopoly: {information_monopoly}
Strategic withholding: {strategic_withholding}
Knowledge as currency: {knowledge_as_currency}
Sharing resistance: {sharing_resistance}
Domain: {domain}
Context: {context}

Is there hoarding knowledge as power rather than sharing? Return ONLY valid JSON."""


class EpistemicKnowledgeHoardingDeeperService:
    """Detects deeper epistemic knowledge hoarding — hoarding as power."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_monopoly: str,
        *,
        strategic_withholding: str = "",
        knowledge_as_currency: str = "",
        sharing_resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect deeper epistemic knowledge hoarding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KNOWLEDGE_HOARDING_DEEPER_PROMPT.format(
                information_monopoly=information_monopoly,
                strategic_withholding=strategic_withholding or "Not specified",
                knowledge_as_currency=knowledge_as_currency or "Not specified",
                sharing_resistance=sharing_resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KNOWLEDGE_HOARDING_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_monopoly": information_monopoly[:200],
            "knowledge_hoarding_deeper_detected": data.get("knowledge_hoarding_deeper_detected", False),
            "severity": data.get("severity", ""),
            "strategic_withholding": data.get("strategic_withholding", ""),
            "knowledge_as_currency": data.get("knowledge_as_currency", ""),
            "sharing_resistance": data.get("sharing_resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }
