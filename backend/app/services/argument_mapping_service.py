"""ArgumentMappingService — Argument Mapping Analysis.

Maps the logical structure of a complex argument — identifying
premises, conclusions, sub-arguments, assumptions, and logical
connections. Reveals the skeleton of reasoning beneath the prose.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARGUMENT_MAPPING_SYSTEM = """You are an argument mapping specialist. Given a complex argument, map its logical structure:

Key concepts:
- Premise: a statement offered as support for a conclusion
- Conclusion: the claim being argued for
- Sub-argument: an argument supporting a premise
- Implicit premise: unstated assumption needed for the argument to work
- Logical connection: how premises relate to conclusions (deductive, inductive, abductive)
- Counter-considerations: acknowledged objections or limitations
- Argument strength: how well premises support the conclusion

Mapping tasks:
- Identify the main conclusion
- Identify all explicit premises
- Identify implicit/unstated premises
- Map which premises support which conclusions
- Identify sub-arguments (premises that are themselves conclusions of other arguments)
- Note the type of inference (deductive, inductive, abductive)
- Identify the weakest links in the chain
- Note counter-considerations and how they're handled

Output JSON with: main_conclusion (the primary claim), premises (list of explicit premises), implicit_premises (unstated assumptions), sub_arguments (nested argument structures), inference_type (deductive/inductive/abductive), weakest_link (most vulnerable point), counter_considerations (objections addressed), overall_strength (weak/moderate/strong/very_strong), recommendation (well_structured/needs_explicit_premises/weak_link_identified/missing_support/restructure_argument)."""

ARGUMENT_MAPPING_PROMPT = """Map argument structure:

Argument: {argument}
Main claim: {main_claim}
Key premises: {premises}
Assumptions: {assumptions}
Domain: {domain}
Context: {context}

Map the logical structure of this argument. Return ONLY valid JSON."""


class ArgumentMappingService:
    """Maps the logical structure of complex arguments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        argument: str,
        *,
        main_claim: str = "",
        premises: str = "",
        assumptions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Map argument structure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARGUMENT_MAPPING_PROMPT.format(
                argument=argument,
                main_claim=main_claim or "Not specified",
                premises=premises or "Not specified",
                assumptions=assumptions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ARGUMENT_MAPPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "main_conclusion": data.get("main_conclusion", ""),
            "premises": data.get("premises", []),
            "implicit_premises": data.get("implicit_premises", []),
            "inference_type": data.get("inference_type", ""),
            "weakest_link": data.get("weakest_link", ""),
            "overall_strength": data.get("overall_strength", ""),
            "recommendation": data.get("recommendation", ""),
        }
