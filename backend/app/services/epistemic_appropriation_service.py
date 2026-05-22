"""EpistemicAppropriationService — Epistemic Appropriation Detection.

Detects epistemic appropriation — taking knowledge from marginalized
communities without credit, reciprocity, or acknowledgment of its
origins, extracting intellectual value without attribution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_APPROPRIATION_SYSTEM = """You are an epistemic appropriation specialist. Given a knowledge claim or practice, assess whether knowledge is being taken without proper attribution:

Key concepts:
- Epistemic appropriation: taking knowledge without credit
- Intellectual extraction: extracting value without reciprocity
- Knowledge colonialism: appropriating indigenous/local knowledge
- Citation erasure: removing attribution from knowledge origins
- Repackaging: presenting others' knowledge as one's own
- Epistemic theft: taking intellectual contributions without credit
- Knowledge laundering: obscuring origins of appropriated knowledge

When epistemic appropriation IS present:
- Knowledge taken from community without attribution
- Origins of knowledge obscured or erased
- Credit given to appropriator, not originator
- Knowledge repackaged without acknowledging source
- Intellectual value extracted without reciprocity
- Community's contribution invisible in final product
- Power differential enables taking without asking

When knowledge sharing is appropriate:
- Attribution given to original sources
- Reciprocity offered to knowledge communities
- Origins acknowledged and respected
- Permission sought and granted
- Benefit shared with originating community
- Collaboration rather than extraction
- Power dynamics acknowledged

Output JSON with: appropriation_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is involved), source (where knowledge originates), appropriator (who is taking it), attribution (what attribution is given), recommendation (appropriate_knowledge_sharing/mild_attribution_gap/significant_epistemic_appropriation/major_knowledge_extraction/attribute_and_reciprocate)."""

EPISTEMIC_APPROPRIATION_PROMPT = """Detect epistemic appropriation:

Situation: {situation}
Knowledge: {knowledge}
Source community: {source}
Attribution given: {attribution}
Domain: {domain}
Context: {context}

Is knowledge being taken from communities without proper credit or reciprocity? Return ONLY valid JSON."""


class EpistemicAppropriationService:
    """Detects epistemic appropriation — taking knowledge without credit."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        source: str = "",
        attribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic appropriation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_APPROPRIATION_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                source=source or "Not specified",
                attribution=attribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_APPROPRIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "appropriation_present": data.get("appropriation_present", False),
            "severity": data.get("severity", ""),
            "knowledge": data.get("knowledge", ""),
            "source": data.get("source", ""),
            "appropriator": data.get("appropriator", ""),
            "recommendation": data.get("recommendation", ""),
        }
