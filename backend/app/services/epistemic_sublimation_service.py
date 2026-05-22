"""EpistemicSublimationService — Epistemic Sublimation Detection.

Detects epistemic sublimation — knowledge transforming directly
from solid conviction to gaseous speculation without passing
through liquid deliberation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUBLIMATION_SYSTEM = """You are an epistemic sublimation specialist. Given a knowledge transformation pattern, assess whether knowledge skips deliberation:

Key concepts:
- Epistemic sublimation: conviction becoming speculation without deliberation
- Phase skip: skipping the deliberation phase
- Conviction collapse: solid conviction collapsing directly to speculation
- Deliberation bypass: bypassing careful deliberation
- Sudden uncertainty: sudden shift from certainty to uncertainty
- Process skip: skipping necessary intellectual processes
- Unmediated transition: transition without mediation

When epistemic sublimation IS present:
- Knowledge transforming from conviction to speculation without deliberation
- Skipping the deliberation phase entirely
- Solid conviction collapsing directly to vague speculation
- Bypassing careful deliberation process
- Sudden shift from certainty to uncertainty without reasoning
- Skipping necessary intellectual processes
- Unmediated transition between states

When proper transition is present:
- Knowledge transforming through proper deliberation
- All phases of intellectual process respected
- Conviction revised through careful reasoning
- Deliberation process followed
- Gradual appropriate shift in confidence
- All necessary processes followed
- Mediated transition between states

Output JSON with: sublimation_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge sublimated), conviction (what conviction was held), speculation (what speculation results), bypass (what deliberation was bypassed), recommendation (proper_transition/mild_skip/significant_sublimation/major_deliberation_bypass/restore_deliberation)."""

EPISTEMIC_SUBLIMATION_PROMPT = """Detect epistemic sublimation:

Knowledge: {knowledge}
Conviction: {conviction}
Speculation: {speculation}
Bypass: {bypass}
Domain: {domain}
Context: {context}

Is knowledge transforming from conviction to speculation without deliberation? Return ONLY valid JSON."""


class EpistemicSublimationService:
    """Detects epistemic sublimation — conviction to speculation without deliberation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        conviction: str = "",
        speculation: str = "",
        bypass: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sublimation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUBLIMATION_PROMPT.format(
                knowledge=knowledge,
                conviction=conviction or "Not specified",
                speculation=speculation or "Not specified",
                bypass=bypass or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUBLIMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "sublimation_present": data.get("sublimation_present", False),
            "severity": data.get("severity", ""),
            "conviction": data.get("conviction", ""),
            "speculation": data.get("speculation", ""),
            "bypass": data.get("bypass", ""),
            "recommendation": data.get("recommendation", ""),
        }
