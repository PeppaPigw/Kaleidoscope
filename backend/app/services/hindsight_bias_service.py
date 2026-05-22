"""HindsightBiasService — Hindsight Bias & Outcome Bias Detection.

Detects "I knew it all along" reasoning where outcomes seem obvious
only after they've occurred. Also detects outcome bias — judging
decision quality by results rather than the information available
at decision time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HINDSIGHT_SYSTEM = """You are a hindsight bias specialist. Given a post-hoc analysis of a decision or event, assess whether hindsight bias is present:
- Is the outcome being treated as if it was predictable beforehand?
- Would this analysis have been possible BEFORE the outcome was known?
- Is decision quality being judged by results rather than process?
- Are people claiming they "knew it all along"?
- What was the actual uncertainty at decision time?

Output JSON with: hindsight_bias_present (bool), outcome_bias_present (bool), severity (none/mild/moderate/severe), claimed_predictability (what people say was obvious), actual_uncertainty_at_time (what was genuinely uncertain), information_available_then (what decision-makers actually knew), information_only_available_now (what we only know after the fact), decision_quality_independent_of_outcome (was the decision reasonable given what was known?), alternative_outcomes_possible (other outcomes that were equally likely), creeping_determinism (bool — is the outcome being treated as inevitable?), proper_evaluation (how to fairly judge the decision), lesson_vs_hindsight (what's a genuine lesson vs what's hindsight bias), recommendation (decision_was_good/decision_was_bad/cannot_judge_from_outcome)."""

HINDSIGHT_PROMPT = """Detect hindsight bias:

Analysis: {analysis}
Outcome: {outcome}
Decision made: {decision}
Domain: {domain}
Context: {context}

Is hindsight bias distorting this evaluation? Return ONLY valid JSON."""


class HindsightBiasService:
    """Detects hindsight bias and outcome bias."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analysis: str,
        *,
        outcome: str = "",
        decision: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hindsight bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HINDSIGHT_PROMPT.format(
                analysis=analysis,
                outcome=outcome or "Not specified",
                decision=decision or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HINDSIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analysis": analysis[:200],
            "hindsight_bias_present": data.get("hindsight_bias_present", False),
            "outcome_bias_present": data.get("outcome_bias_present", False),
            "severity": data.get("severity", ""),
            "claimed_predictability": data.get("claimed_predictability", ""),
            "actual_uncertainty_at_time": data.get("actual_uncertainty_at_time", ""),
            "information_available_then": data.get("information_available_then", ""),
            "information_only_available_now": data.get("information_only_available_now", ""),
            "decision_quality_independent_of_outcome": data.get("decision_quality_independent_of_outcome", ""),
            "alternative_outcomes_possible": data.get("alternative_outcomes_possible", []),
            "creeping_determinism": data.get("creeping_determinism", False),
            "proper_evaluation": data.get("proper_evaluation", ""),
            "lesson_vs_hindsight": data.get("lesson_vs_hindsight", ""),
            "recommendation": data.get("recommendation", ""),
        }
