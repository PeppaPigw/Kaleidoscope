"""DistinctionBiasService — Distinction Bias Detection.

Detects distinction bias — overvaluing differences between
options when evaluating them simultaneously (joint evaluation)
vs. separately (separate evaluation). Hsee & Zhang (2004).
Side-by-side comparison makes trivial differences seem important.
The 4K vs 1080p TV looks dramatically different in the store
but identical at home.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISTINCTION_SYSTEM = """You are a distinction bias specialist. Given a comparison between options, assess whether joint evaluation is making trivial differences seem important:

Key concepts (Hsee & Zhang, 2004):
- Distinction bias: overvaluing differences when options are compared side-by-side
- Joint vs. separate evaluation: differences loom larger in joint evaluation
- Evaluability: some attributes are only meaningful in comparison
- Experience prediction error: predicted experience difference > actual experience difference
- Hedonic adaptation: differences that seem large now will fade with use
- Maximizer trap: seeking the "best" when "good enough" provides equal satisfaction

When distinction bias IS present:
- Paying a premium for differences that won't matter in daily use
- Agonizing over choices that would provide equal satisfaction separately
- Side-by-side comparison making trivial differences seem crucial
- Predicted enjoyment difference far exceeds likely actual difference
- The distinguishing feature is only noticeable in direct comparison
- Spending disproportionate time/money on marginal improvements

When distinctions ARE meaningful:
- The difference is large enough to affect daily experience
- The attribute is evaluable even without comparison (e.g., speed, size)
- Past experience confirms the difference matters in practice
- The cost of the upgrade is trivial relative to the benefit
- The distinction affects functionality, not just perception

Output JSON with: distinction_bias_present (bool), severity (none/mild/moderate/severe), options_compared (what is being compared), key_distinction (what difference is being overvalued), distinction_magnitude (how large is the actual difference), predicted_experience_gap (how different the person thinks experience will be), actual_experience_gap (how different experience likely will be), evaluability (is the attribute meaningful without comparison?), hedonic_adaptation (will the difference fade with time?), cost_of_distinction (what premium is being paid for the difference), separate_evaluation (would either option satisfy in isolation?), maximizer_behavior (bool — seeking "best" when "good enough" suffices?), recommendation (distinction_meaningful/mild_overvaluation/significant_distinction_bias/major_distinction_bias/either_option_satisfies)."""

DISTINCTION_PROMPT = """Detect distinction bias:

Comparison: {comparison}
Options: {options}
Key difference: {difference}
Usage context: {usage}
Domain: {domain}
Context: {context}

Is joint evaluation making trivial differences seem important? Return ONLY valid JSON."""


class DistinctionBiasService:
    """Detects distinction bias — overvaluing differences in side-by-side comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comparison: str,
        *,
        options: str = "",
        difference: str = "",
        usage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect distinction bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISTINCTION_PROMPT.format(
                comparison=comparison,
                options=options or "Not specified",
                difference=difference or "Not specified",
                usage=usage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISTINCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comparison": comparison[:200],
            "distinction_bias_present": data.get("distinction_bias_present", False),
            "severity": data.get("severity", ""),
            "options_compared": data.get("options_compared", ""),
            "key_distinction": data.get("key_distinction", ""),
            "distinction_magnitude": data.get("distinction_magnitude", ""),
            "predicted_experience_gap": data.get("predicted_experience_gap", ""),
            "actual_experience_gap": data.get("actual_experience_gap", ""),
            "evaluability": data.get("evaluability", ""),
            "hedonic_adaptation": data.get("hedonic_adaptation", ""),
            "cost_of_distinction": data.get("cost_of_distinction", ""),
            "separate_evaluation": data.get("separate_evaluation", ""),
            "maximizer_behavior": data.get("maximizer_behavior", False),
            "recommendation": data.get("recommendation", ""),
        }
