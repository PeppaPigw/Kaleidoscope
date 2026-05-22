"""CompositionEffectService — Interaction & Combination Effect Analysis.

When two or more interventions, findings, or strategies are combined,
do they amplify, cancel, interfere, or create unexpected emergent effects?
Detects synergies, antagonisms, and non-obvious interaction patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPOSITION_SYSTEM = """You are a composition effect analyst. Given two or more elements being combined, assess their interaction:
- Do they amplify each other (synergy)?
- Do they cancel each other (antagonism)?
- Do they interfere in unexpected ways?
- Are there emergent effects that neither produces alone?
- What's the interaction type (additive, multiplicative, threshold, conditional)?
- Historical examples of similar combinations succeeding or failing?

Output JSON with: interaction_type (synergistic/additive/neutral/antagonistic/catastrophic), combined_effect_vs_sum (greater_than_sum/equal_to_sum/less_than_sum/opposite_of_sum), synergies (list of: mechanism, magnitude (minor/moderate/major)), antagonisms (list of: mechanism, severity (minor/moderate/major/fatal)), emergent_effects (list of effects that appear only in combination), sequencing_matters (bool — does order of application matter?), optimal_sequence (if sequencing matters, what order), conditions_for_synergy (what must be true for positive interaction), conditions_for_antagonism (what triggers negative interaction), historical_parallels (list of similar combinations and their outcomes), net_interaction_score (-1 to 1, negative=antagonistic, positive=synergistic), recommendation (combine/combine_with_caution/sequence_carefully/do_not_combine)."""

COMPOSITION_PROMPT = """Assess composition effects:

Element A: {element_a}
Element B: {element_b}
{additional_elements}Context: {context}
Domain: {domain}
Goal: {goal}

What happens when these are combined? Return ONLY valid JSON."""


class CompositionEffectService:
    """Assesses interaction effects when combining elements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        element_a: str,
        element_b: str,
        *,
        additional_elements: list[str] | None = None,
        context: str = "",
        domain: str = "",
        goal: str = "",
    ) -> dict:
        """Assess composition effects between elements."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = ""
        if additional_elements:
            for i, elem in enumerate(additional_elements, start=3):
                extra += f"Element {chr(64 + i)}: {elem}\n"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPOSITION_PROMPT.format(
                element_a=element_a,
                element_b=element_b,
                additional_elements=extra,
                context=context or "General combination",
                domain=domain or "general",
                goal=goal or "Not specified",
            ),
            system=COMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "elements": [element_a[:150], element_b[:150]] + [e[:150] for e in (additional_elements or [])],
            "interaction_type": data.get("interaction_type", ""),
            "combined_effect_vs_sum": data.get("combined_effect_vs_sum", ""),
            "synergies": data.get("synergies", []),
            "antagonisms": data.get("antagonisms", []),
            "emergent_effects": data.get("emergent_effects", []),
            "sequencing_matters": data.get("sequencing_matters", False),
            "optimal_sequence": data.get("optimal_sequence", ""),
            "conditions_for_synergy": data.get("conditions_for_synergy", ""),
            "conditions_for_antagonism": data.get("conditions_for_antagonism", ""),
            "historical_parallels": data.get("historical_parallels", []),
            "net_interaction_score": data.get("net_interaction_score", 0),
            "recommendation": data.get("recommendation", ""),
        }
