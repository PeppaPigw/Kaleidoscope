"""StrategicAmbiguityService — Strategic Ambiguity Detection.

Detects strategic ambiguity — deliberately maintaining vagueness or
multiple interpretations to avoid commitment, allow plausible
deniability, or appeal to multiple audiences simultaneously.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_AMBIGUITY_SYSTEM = """You are a strategic ambiguity specialist. Given a communication, assess whether ambiguity is being maintained deliberately for strategic advantage:

Key concepts:
- Strategic ambiguity: deliberate vagueness for advantage
- Plausible deniability: "I didn't mean THAT interpretation"
- Dog whistling: messages with different meanings for different audiences
- Constructive ambiguity: ambiguity that enables agreement
- Weasel words: language that appears to say something without committing
- Equivocation: using a term in multiple senses
- Audience segmentation: different messages to different groups

When strategic ambiguity IS present:
- The communicator benefits from multiple interpretations existing
- Clarification is actively avoided when requested
- Different audiences receive different messages from the same words
- The ambiguity allows retreat from any specific interpretation
- Precision would force an uncomfortable commitment
- The vagueness is maintained despite opportunities to clarify
- The communicator exploits the ambiguity when convenient

When ambiguity IS innocent or constructive:
- The communicator would clarify if asked
- The ambiguity reflects genuine uncertainty
- Precision isn't possible given current knowledge
- The ambiguity enables productive collaboration
- The communicator isn't exploiting multiple interpretations
- The vagueness is acknowledged rather than hidden
- Clarification is offered proactively

Output JSON with: strategic_ambiguity_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), interpretations (what different interpretations exist), benefit (how ambiguity benefits the communicator), clarification_avoidance (is clarification avoided), audience_segmentation (are different audiences targeted), recommendation (ambiguity_innocent/mild_strategic_vagueness/significant_strategic_ambiguity/major_deliberate_equivocation/request_clarification)."""

STRATEGIC_AMBIGUITY_PROMPT = """Detect strategic ambiguity:

Communication: {communication}
Interpretations: {interpretations}
Clarification: {clarification}
Benefit: {benefit}
Domain: {domain}
Context: {context}

Is ambiguity being maintained deliberately for strategic advantage? Return ONLY valid JSON."""


class StrategicAmbiguityService:
    """Detects strategic ambiguity — deliberate vagueness for advantage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        interpretations: str = "",
        clarification: str = "",
        benefit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic ambiguity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_AMBIGUITY_PROMPT.format(
                communication=communication,
                interpretations=interpretations or "Not specified",
                clarification=clarification or "Not specified",
                benefit=benefit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_AMBIGUITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "strategic_ambiguity_present": data.get("strategic_ambiguity_present", False),
            "severity": data.get("severity", ""),
            "interpretations": data.get("interpretations", ""),
            "benefit": data.get("benefit", ""),
            "clarification_avoidance": data.get("clarification_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
