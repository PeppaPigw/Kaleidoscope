"""EpistemicIdeaPossessivenessService — Epistemic Idea Possessiveness Detection.

Detects epistemic idea possessiveness — treating ideas as personal property
and resenting others who work with similar concepts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDEA_POSSESSIVENESS_SYSTEM = """You are an epistemic idea possessiveness specialist. Given possessiveness over ideas, assess idea possessiveness:

Key concepts:
- Epistemic idea possessiveness: treating ideas as owned property
- Intellectual property anxiety: fear of ideas being taken
- Credit obsession: needing attribution for every thought
- Sharing resistance: reluctance to share ideas freely
- Theft perception: seeing others' similar ideas as stolen
- Hoarding behavior: keeping ideas secret until published
- Ownership marking: excessive claiming of intellectual territory

When epistemic idea possessiveness IS present:
- Treating ideas as owned
- Fear of ideas being taken
- Needing attribution for everything
- Reluctance to share
- Seeing similar ideas as stolen
- Keeping ideas secret
- Excessive claiming

When no idea possessiveness:
- Ideas as shared commons
- Comfortable with idea flow
- Generous with attribution
- Sharing freely
- Celebrating parallel discovery
- Open collaboration
- Humble about originality

Output JSON with: idea_possessiveness_detected (bool), severity (none/mild/moderate/severe), property_anxiety (what fearing taken), credit_obsession (what needing attribution for), sharing_resistance (what reluctant to share), theft_perception (what seeing as stolen), recommendation (no_idea_possessiveness/mild_generosity_practice/significant_sharing_work/major_intensive_openness_therapy/emergency_active_hoarding)."""

EPISTEMIC_IDEA_POSSESSIVENESS_PROMPT = """Detect epistemic idea possessiveness:

Property anxiety: {property_anxiety}
Credit obsession: {credit_obsession}
Sharing resistance: {sharing_resistance}
Theft perception: {theft_perception}
Domain: {domain}
Context: {context}

Is there treating ideas as personal property and resenting others? Return ONLY valid JSON."""


class EpistemicIdeaPossessivenessService:
    """Detects epistemic idea possessiveness — treating ideas as owned property."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        property_anxiety: str,
        *,
        credit_obsession: str = "",
        sharing_resistance: str = "",
        theft_perception: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic idea possessiveness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDEA_POSSESSIVENESS_PROMPT.format(
                property_anxiety=property_anxiety,
                credit_obsession=credit_obsession or "Not specified",
                sharing_resistance=sharing_resistance or "Not specified",
                theft_perception=theft_perception or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDEA_POSSESSIVENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "property_anxiety": property_anxiety[:200],
            "idea_possessiveness_detected": data.get("idea_possessiveness_detected", False),
            "severity": data.get("severity", ""),
            "credit_obsession": data.get("credit_obsession", ""),
            "sharing_resistance": data.get("sharing_resistance", ""),
            "theft_perception": data.get("theft_perception", ""),
            "recommendation": data.get("recommendation", ""),
        }
