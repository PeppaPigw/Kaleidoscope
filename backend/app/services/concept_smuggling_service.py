"""ConceptSmugglingService — Concept Smuggling Detection.

Detects concept smuggling — introducing controversial or loaded
concepts under innocuous labels, embedding contested assumptions
in seemingly neutral terminology so they bypass critical scrutiny.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONCEPT_SMUGGLING_SYSTEM = """You are a concept smuggling specialist. Given terminology or framing, assess whether controversial concepts are being introduced under innocuous labels:

Key concepts:
- Concept smuggling: hiding contested ideas in neutral-seeming terms
- Loaded language: terms that embed assumptions
- Framing effects: how naming shapes perception
- Definitional gerrymandering: defining terms to include your conclusion
- Euphemism treadmill: neutral terms acquiring loaded meanings
- Trojan horse concepts: ideas that seem harmless but carry hidden implications
- Semantic infiltration: adopting opponent's terminology uncritically

When concept smuggling IS present:
- A neutral-sounding term embeds a controversial assumption
- The definition of a term has been expanded to include contested cases
- Accepting the terminology means accepting the conclusion
- The framing makes one position seem like the default/neutral one
- Contested empirical claims are built into definitions
- The terminology prejudges the question it's supposed to help answer
- Rejecting the concept requires rejecting the seemingly neutral term

When terminology IS neutral:
- The term doesn't embed contested assumptions
- Multiple positions can be expressed using the same terminology
- The definition is widely accepted and not gerrymandered
- The framing doesn't prejudge the conclusion
- The term describes rather than evaluates
- Alternative framings are acknowledged
- The terminology allows genuine disagreement

Output JSON with: concept_smuggling_present (bool), severity (none/mild/moderate/severe), term (what term or concept), surface_meaning (what it appears to mean), smuggled_content (what is actually being smuggled in), assumption_embedded (what assumption is hidden), alternative_framing (how it could be framed neutrally), recommendation (terminology_neutral/mild_loading/significant_concept_smuggling/major_definitional_gerrymandering/use_neutral_framing)."""

CONCEPT_SMUGGLING_PROMPT = """Detect concept smuggling:

Term/framing: {term}
Usage: {usage}
Assumptions: {assumptions}
Alternative: {alternative}
Domain: {domain}
Context: {context}

Is this terminology smuggling in controversial concepts under innocuous labels? Return ONLY valid JSON."""


class ConceptSmugglingService:
    """Detects concept smuggling — controversial ideas hidden in neutral terminology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        term: str,
        *,
        usage: str = "",
        assumptions: str = "",
        alternative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect concept smuggling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONCEPT_SMUGGLING_PROMPT.format(
                term=term,
                usage=usage or "Not specified",
                assumptions=assumptions or "Not specified",
                alternative=alternative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONCEPT_SMUGGLING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "term": term[:200],
            "concept_smuggling_present": data.get("concept_smuggling_present", False),
            "severity": data.get("severity", ""),
            "surface_meaning": data.get("surface_meaning", ""),
            "smuggled_content": data.get("smuggled_content", ""),
            "assumption_embedded": data.get("assumption_embedded", ""),
            "alternative_framing": data.get("alternative_framing", ""),
            "recommendation": data.get("recommendation", ""),
        }
