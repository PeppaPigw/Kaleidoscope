"""EvaluabilityService — Evaluability Bias Detection.

Detects evaluability bias — difficulty evaluating an attribute
in isolation that would be easy to evaluate in comparison.
Hsee (1996). When attributes are hard to evaluate alone,
people rely on irrelevant but evaluable attributes. Joint
vs separate evaluation produces different preferences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EVALUABILITY_SYSTEM = """You are an evaluability bias specialist. Given a judgment or preference, assess whether evaluability is driving the decision rather than actual value:

Key concepts (Hsee, 1996):
- Evaluability: how easy an attribute is to judge in isolation
- Joint vs separate evaluation: preferences reverse between modes
- Evaluability hypothesis: hard-to-evaluate attributes are underweighted alone
- Proxy reliance: using evaluable proxies for hard-to-evaluate qualities
- Comparison dependence: needing comparison to assess value
- Specification seeking: preferring precisely specified over vague-but-better
- Number fixation: overweighting quantified attributes over qualitative ones

When evaluability bias IS present:
- Choosing based on easily quantified attributes over harder-to-assess quality
- Preferences that would reverse if options were compared side-by-side
- Overweighting GPA, rankings, or scores over harder-to-evaluate qualities
- "I can't tell if this is good" leading to reliance on irrelevant metrics
- Ignoring important but hard-to-evaluate attributes
- Preferring the option with clear specifications over ambiguous-but-better

When the evaluation IS appropriate:
- The evaluable attribute genuinely captures what matters
- The person has enough expertise to evaluate in isolation
- Comparison information is genuinely unavailable
- The quantified metric is a valid proxy for quality
- The decision would be the same in joint evaluation

Output JSON with: evaluability_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), evaluable_attribute (what easy-to-evaluate attribute is being used), hard_attribute (what hard-to-evaluate attribute is being ignored), joint_evaluation (would preference change in comparison?), proxy_validity (is the evaluable attribute a good proxy?), expertise_level (can the person evaluate the hard attribute?), recommendation (evaluation_appropriate/mild_evaluability/significant_proxy_reliance/major_evaluability_bias/seek_comparison_information)."""

EVALUABILITY_PROMPT = """Detect evaluability bias:

Judgment: {judgment}
Attributes: {attributes}
Evaluation mode: {mode}
Expertise: {expertise}
Domain: {domain}
Context: {context}

Is evaluability driving the decision rather than actual value? Return ONLY valid JSON."""


class EvaluabilityService:
    """Detects evaluability bias — easy-to-evaluate attributes overweighted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        attributes: str = "",
        mode: str = "",
        expertise: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect evaluability bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EVALUABILITY_PROMPT.format(
                judgment=judgment,
                attributes=attributes or "Not specified",
                mode=mode or "Not specified",
                expertise=expertise or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EVALUABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "evaluability_present": data.get("evaluability_present", False),
            "severity": data.get("severity", ""),
            "evaluable_attribute": data.get("evaluable_attribute", ""),
            "hard_attribute": data.get("hard_attribute", ""),
            "joint_evaluation": data.get("joint_evaluation", ""),
            "proxy_validity": data.get("proxy_validity", ""),
            "expertise_level": data.get("expertise_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
