"""ArgumentDilutionService — Argument Dilution Effect Detection.

Detects argument dilution — weak arguments reducing the
persuasive force of strong ones when presented together.
Nisbett, Zukier & Lemley (1981). Adding weak evidence to
strong evidence actually reduces overall persuasiveness.
The diagnostic value of strong evidence gets diluted by
non-diagnostic information. Less can be more in argumentation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARGUMENT_DILUTION_SYSTEM = """You are an argument dilution specialist. Given a set of arguments or evidence, assess whether weak elements are diluting the force of strong ones:

Key concepts (Nisbett, Zukier & Lemley, 1981):
- Dilution effect: non-diagnostic info weakens diagnostic info
- Averaging vs adding: people average argument strength, not sum it
- Weak evidence penalty: adding weak evidence hurts more than helps
- Information overload: too much info reduces decision quality
- Signal-to-noise: weak arguments are noise that obscures signal
- Representativeness dilution: irrelevant details reduce typicality
- Less-is-more effect: fewer strong arguments beat many mixed ones

When dilution IS occurring:
- Strong evidence presented alongside irrelevant details
- Compelling arguments mixed with speculative ones
- Key findings buried in a sea of minor observations
- "And also..." adding weak points after strong ones
- Padding a case with filler that doesn't strengthen it
- Mixing proven facts with unverified claims
- Strong data diluted by anecdotal additions

When comprehensive presentation IS appropriate:
- All evidence is genuinely diagnostic and relevant
- The audience needs completeness for their own evaluation
- Each piece adds independent evidential value
- The format requires exhaustive presentation
- Weak evidence is clearly labeled as supplementary

Output JSON with: dilution_present (bool), severity (none/mild/moderate/severe), case (what case is being made), strong_elements (what are the strong arguments/evidence), diluting_elements (what weak elements are diluting), dilution_mechanism (how is dilution occurring), net_effect (how does dilution affect overall persuasiveness), optimal_presentation (what would be stronger without dilution), recommendation (presentation_appropriate/mild_dilution/significant_argument_dilution/major_signal_buried/remove_weak_elements)."""

ARGUMENT_DILUTION_PROMPT = """Detect argument dilution:

Case: {case}
Strong elements: {strong}
Weak elements: {weak}
Presentation: {presentation}
Domain: {domain}
Context: {context}

Are weak arguments or evidence diluting the persuasive force of strong ones? Return ONLY valid JSON."""


class ArgumentDilutionService:
    """Detects argument dilution — weak elements reducing force of strong ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        case: str,
        *,
        strong: str = "",
        weak: str = "",
        presentation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect argument dilution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARGUMENT_DILUTION_PROMPT.format(
                case=case,
                strong=strong or "Not specified",
                weak=weak or "Not specified",
                presentation=presentation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ARGUMENT_DILUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "case": case[:200],
            "dilution_present": data.get("dilution_present", False),
            "severity": data.get("severity", ""),
            "strong_elements": data.get("strong_elements", ""),
            "diluting_elements": data.get("diluting_elements", ""),
            "dilution_mechanism": data.get("dilution_mechanism", ""),
            "net_effect": data.get("net_effect", ""),
            "optimal_presentation": data.get("optimal_presentation", ""),
            "recommendation": data.get("recommendation", ""),
        }
