"""FalseDichotomyExhaustiveService — False Dichotomy Detection.

Detects false dichotomy — presenting only two options when more
exist, forcing a choice between extremes while ignoring the middle
ground, alternative framings, or additional options.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_DICHOTOMY_SYSTEM = """You are a false dichotomy specialist. Given a choice being presented, assess whether it artificially limits options to only two when more exist:

Key concepts:
- False dichotomy: presenting only two options when more exist
- Excluded middle: ignoring intermediate positions
- False dilemma: forcing a choice between extremes
- Spectrum thinking: many issues exist on a continuum
- Third option: the unconsidered alternative
- Framing effect: how the choice is presented limits perceived options
- Binary thinking: reducing complex issues to either/or

When false dichotomy IS present:
- "Either X or Y" when Z is also possible
- "You're either with us or against us" ignoring neutrality
- Presenting extremes while ignoring moderate positions
- "If not A, then B" when C, D, E are also options
- Forcing binary choice on a continuous spectrum
- "Either we do nothing or we do everything"
- Ignoring creative alternatives that combine elements

When dichotomy IS genuine:
- The options are truly exhaustive and mutually exclusive
- Logical necessity limits the options (P or ¬P)
- Practical constraints genuinely limit choices to two
- The middle ground has been considered and ruled out
- The binary is a simplification acknowledged as such
- Additional options have been explored and found unviable
- The dichotomy is definitional, not empirical

Output JSON with: false_dichotomy_present (bool), severity (none/mild/moderate/severe), choice_presented (what options are presented), missing_options (what options are excluded), spectrum (is this actually a spectrum), framing (how framing limits options), genuine_constraint (is there a real constraint), recommendation (dichotomy_genuine/mild_oversimplification/significant_false_dichotomy/major_option_suppression/explore_additional_options)."""

FALSE_DICHOTOMY_PROMPT = """Detect false dichotomy:

Choice presented: {choice}
Options given: {options}
Missing alternatives: {missing}
Constraints: {constraints}
Domain: {domain}
Context: {context}

Is this presenting only two options when more exist? Return ONLY valid JSON."""


class FalseDichotomyExhaustiveService:
    """Detects false dichotomy — artificially limiting options to two."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        choice: str,
        *,
        options: str = "",
        missing: str = "",
        constraints: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false dichotomy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_DICHOTOMY_PROMPT.format(
                choice=choice,
                options=options or "Not specified",
                missing=missing or "Not specified",
                constraints=constraints or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_DICHOTOMY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choice": choice[:200],
            "false_dichotomy_present": data.get("false_dichotomy_present", False),
            "severity": data.get("severity", ""),
            "missing_options": data.get("missing_options", ""),
            "spectrum": data.get("spectrum", ""),
            "framing": data.get("framing", ""),
            "recommendation": data.get("recommendation", ""),
        }
