"""FalseDilemmaService — False Dilemma Detection.

Detects false dilemma — presenting a limited set of options
(not necessarily just two) as if they are the only possibilities,
when in fact additional alternatives exist. Broader than binary
false dichotomy — can involve 3, 4, or more options while still
excluding viable alternatives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_DILEMMA_SYSTEM = """You are a false dilemma specialist. Given a decision or argument, assess whether it artificially limits the available options:

Key concepts:
- False dilemma: presenting limited options as exhaustive
- Option suppression: hiding viable alternatives
- Forced choice: creating artificial urgency to choose from given options
- Menu dependence: people choose from what's presented, not what exists
- Creative alternatives: options that combine or transcend the given choices
- Constraint legitimacy: are the limitations real or artificial?
- Framing effects: how presentation limits perceived options

When false dilemma IS present:
- Presenting 2-4 options as if they're the only possibilities
- "We can either do A, B, or C" when D and E are also viable
- Excluding compromise, hybrid, or creative solutions
- Artificial urgency preventing exploration of alternatives
- Framing that makes other options seem inconceivable
- "These are our only choices" without justification
- Ignoring the option of doing nothing or waiting

When false dilemma is NOT present:
- The options genuinely are exhaustive (logical necessity)
- Practical constraints legitimately limit choices
- Additional options have been considered and ruled out with reasons
- The limitation is acknowledged as a simplification
- The decision-maker is invited to suggest alternatives
- Resource constraints genuinely limit the feasible set
- The options represent the main viable approaches after analysis

Output JSON with: false_dilemma_present (bool), severity (none/mild/moderate/severe), options_presented (what choices are given), options_missing (what alternatives are excluded), constraint_real (are limitations genuine), framing (how presentation limits perception), recommendation (no_false_dilemma/mild_option_limitation/significant_false_dilemma/major_option_suppression/explore_alternatives)."""

FALSE_DILEMMA_PROMPT = """Detect false dilemma:

Decision: {decision}
Options presented: {options_presented}
Missing alternatives: {missing}
Constraints cited: {constraints}
Domain: {domain}
Context: {context}

Does this artificially limit the available options? Return ONLY valid JSON."""


class FalseDilemmaService:
    """Detects false dilemma — artificially limiting available options."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        options_presented: str = "",
        missing: str = "",
        constraints: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false dilemma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_DILEMMA_PROMPT.format(
                decision=decision,
                options_presented=options_presented or "Not specified",
                missing=missing or "Not specified",
                constraints=constraints or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_DILEMMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "false_dilemma_present": data.get("false_dilemma_present", False),
            "severity": data.get("severity", ""),
            "options_presented": data.get("options_presented", ""),
            "options_missing": data.get("options_missing", ""),
            "constraint_real": data.get("constraint_real", ""),
            "recommendation": data.get("recommendation", ""),
        }
