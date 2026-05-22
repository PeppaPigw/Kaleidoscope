"""ConceptStretchingService — Concept Stretching Detection.

Detects concept stretching — stretching a concept beyond its valid
domain until it explains everything and therefore nothing, losing
its analytical power through overextension.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONCEPT_STRETCHING_SYSTEM = """You are a concept stretching specialist. Given a conceptual application, assess whether a concept is being stretched beyond its valid domain:

Key concepts:
- Concept stretching: applying concept beyond its valid scope
- Sartori's ladder: trading intension for extension
- Explanatory overreach: concept explaining everything (therefore nothing)
- Category error: applying concept to wrong domain
- Metaphor literalization: treating metaphorical application as literal
- Analytical dilution: concept losing power through overuse
- Domain specificity: concepts valid in some domains but not others

When concept stretching IS present:
- Concept applied far beyond its original domain
- Explanatory power lost through overextension
- Everything becomes an instance of the concept
- Original precision and utility diluted
- Metaphorical use treated as literal analysis
- Concept no longer distinguishes anything
- Domain boundaries of concept ignored

When concept application is appropriate:
- Concept applied within its valid domain
- Extension justified by structural similarity
- Analytical power preserved
- Concept still distinguishes meaningfully
- Domain boundaries respected
- Extension acknowledged as extension
- Original precision maintained

Output JSON with: stretching_present (bool), severity (none/mild/moderate/severe), concept (what concept is stretched), original_domain (where concept is valid), stretched_to (where it's being applied), power_lost (what analytical power is lost), recommendation (appropriate_application/mild_extension/significant_stretching/major_concept_dilution/respect_domain_boundaries)."""

CONCEPT_STRETCHING_PROMPT = """Detect concept stretching:

Application: {application}
Concept: {concept}
Original domain: {original}
Current use: {current}
Domain: {domain}
Context: {context}

Is this concept being stretched beyond its valid domain? Return ONLY valid JSON."""


class ConceptStretchingService:
    """Detects concept stretching — overextending concepts beyond valid domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        application: str,
        *,
        concept: str = "",
        original: str = "",
        current: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect concept stretching."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONCEPT_STRETCHING_PROMPT.format(
                application=application,
                concept=concept or "Not specified",
                original=original or "Not specified",
                current=current or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONCEPT_STRETCHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "application": application[:200],
            "stretching_present": data.get("stretching_present", False),
            "severity": data.get("severity", ""),
            "concept": data.get("concept", ""),
            "original_domain": data.get("original_domain", ""),
            "power_lost": data.get("power_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
