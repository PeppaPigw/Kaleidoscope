"""LessIsBetterService — Less-is-Better Effect Detection.

Detects the less-is-better effect — when a smaller/lesser option
is preferred over a larger/greater option in separate evaluation,
but the preference reverses in joint evaluation. Hsee (1998).
A $45 scarf in a fancy box is preferred over a $55 coat in a
plain bag when evaluated separately, but not when compared
side-by-side. Evaluability and presentation trump objective value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LESS_IS_BETTER_SYSTEM = """You are a less-is-better effect specialist. Given an evaluation or preference, assess whether presentation or evaluability is causing a smaller option to be preferred over an objectively larger one:

Key concepts (Hsee, 1998):
- Less-is-better: smaller option preferred in separate evaluation
- Evaluability hypothesis: some attributes are hard to evaluate without comparison
- Presentation effect: packaging/framing makes lesser option seem better
- Reference point dependence: evaluation depends on what's salient
- Joint vs. separate evaluation: preferences reverse between modes
- Waste aversion: adding low-quality items to a set can reduce perceived value

When less-is-better IS present:
- A smaller gift is preferred because it's better presented
- Adding items to a set reduces perceived value (dilution)
- Quantity is being evaluated without reference to quality
- Presentation is dominating objective value assessment
- The evaluator lacks context to assess the attribute that makes the larger option better
- "Less but better" when "more and better" is available

When preferring less IS rational:
- Quality genuinely matters more than quantity for the use case
- The additional items genuinely reduce utility (clutter, maintenance)
- The presentation reflects genuine quality differences
- The evaluator has full information and still prefers less
- Minimalism is a genuine preference, not an evaluation error

Output JSON with: less_is_better_present (bool), severity (none/mild/moderate/severe), smaller_option (what is the lesser option), larger_option (what is the greater option), evaluation_mode (separate/joint/mixed), presentation_factor (how is presentation influencing?), evaluability_gap (what attribute is hard to evaluate?), objective_comparison (which is objectively better?), preference_reversal (bool — would preference reverse in joint evaluation?), reference_point (what reference is being used?), dilution_effect (bool — are low-quality additions reducing perceived value?), recommendation (preference_rational/mild_less_is_better/significant_evaluation_error/major_presentation_bias/compare_side_by_side)."""

LESS_IS_BETTER_PROMPT = """Detect less-is-better effect:

Evaluation: {evaluation}
Options: {options}
Presentation: {presentation}
Evaluation mode: {mode}
Domain: {domain}
Context: {context}

Is presentation or evaluability causing preference for an objectively lesser option? Return ONLY valid JSON."""


class LessIsBetterService:
    """Detects less-is-better effect — presentation causing preference for lesser options."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        options: str = "",
        presentation: str = "",
        mode: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect less-is-better effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LESS_IS_BETTER_PROMPT.format(
                evaluation=evaluation,
                options=options or "Not specified",
                presentation=presentation or "Not specified",
                mode=mode or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LESS_IS_BETTER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "less_is_better_present": data.get("less_is_better_present", False),
            "severity": data.get("severity", ""),
            "smaller_option": data.get("smaller_option", ""),
            "larger_option": data.get("larger_option", ""),
            "evaluation_mode": data.get("evaluation_mode", ""),
            "presentation_factor": data.get("presentation_factor", ""),
            "evaluability_gap": data.get("evaluability_gap", ""),
            "objective_comparison": data.get("objective_comparison", ""),
            "preference_reversal": data.get("preference_reversal", False),
            "reference_point": data.get("reference_point", ""),
            "dilution_effect": data.get("dilution_effect", False),
            "recommendation": data.get("recommendation", ""),
        }
