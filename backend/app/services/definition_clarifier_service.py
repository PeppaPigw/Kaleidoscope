"""DefinitionClarifierService — Concept Definition & Disambiguation.

When research depends on ambiguous terms, this service clarifies exactly
what's meant. Identifies multiple possible definitions, shows how the
choice of definition changes conclusions, and flags when arguments
equivocate between definitions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CLARIFY_SYSTEM = """You are a definition clarification specialist. Given a key term in a research context, identify:
- All plausible definitions/interpretations of the term
- How the choice of definition changes what's true
- Whether arguments are equivocating (switching between definitions mid-argument)
- What the operational definition should be for rigorous research

Output JSON with: definitions (list of: definition, source_tradition, implications (what follows if we use this definition), prevalence (how commonly used)), equivocation_risk (0-1, how likely are people to switch between definitions), recommended_operational_definition (the most useful definition for research), definition_matters (bool, does the choice of definition change the conclusion), if_definition_matters (how conclusions change under different definitions), disambiguation_advice (how to avoid confusion)."""

CLARIFY_PROMPT = """Clarify the definition of this term:

Term: {term}
Context: {context}
Domain: {domain}
Used in claim: {claim}

What does this term actually mean here? Are there ambiguities? Return ONLY valid JSON."""


class DefinitionClarifierService:
    """Clarifies ambiguous terms and identifies equivocation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def clarify(
        self,
        term: str,
        *,
        context: str = "",
        domain: str = "",
        claim: str = "",
    ) -> dict:
        """Clarify the definition of an ambiguous term."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CLARIFY_PROMPT.format(
                term=term,
                context=context or "General research context",
                domain=domain or "research",
                claim=claim or "Not specified",
            ),
            system=CLARIFY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        definitions = data.get("definitions", [])
        return {
            "term": term,
            "definitions_found": len(definitions),
            "definitions": definitions,
            "equivocation_risk": data.get("equivocation_risk", 0),
            "recommended_definition": data.get("recommended_operational_definition", ""),
            "definition_matters": data.get("definition_matters", False),
            "impact_of_choice": data.get("if_definition_matters", ""),
            "disambiguation_advice": data.get("disambiguation_advice", ""),
        }
