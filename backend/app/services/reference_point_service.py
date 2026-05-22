"""ReferencePointService — Reference Point Bias Detection.

Detects reference point bias — evaluating outcomes relative
to an arbitrary or inappropriate reference point rather than
in absolute terms. Kahneman & Tversky (1979). The same
outcome feels like a gain or loss depending on the reference.
A salary of $80K feels great if you expected $70K but terrible
if you expected $90K — same outcome, different experience.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REFERENCE_POINT_SYSTEM = """You are a reference point bias specialist. Given a judgment or evaluation, assess whether an inappropriate reference point is distorting the assessment:

Key concepts (Kahneman & Tversky, 1979):
- Reference dependence: outcomes evaluated relative to reference, not absolute
- Arbitrary anchoring: reference points set by irrelevant factors
- Status quo as reference: current state as default comparison
- Aspiration-based reference: expectations setting the reference
- Peak reference: best past outcome as reference
- Social comparison reference: others' outcomes as reference
- Framing through reference: same outcome as gain or loss

When reference point bias IS present:
- Evaluating outcomes relative to arbitrary or inappropriate benchmarks
- "I lost money" when actually gaining less than expected
- Using peak performance as the reference for normal performance
- Comparing to irrelevant alternatives rather than absolute value
- Satisfaction driven by reference rather than actual outcome
- "It's not as good as last time" when last time was exceptional
- Anchoring on initial price/offer as the reference

When the reference IS appropriate:
- The reference reflects genuine opportunity cost
- The comparison is to a relevant and achievable alternative
- The person considers absolute value alongside relative
- The reference is based on informed expectations
- Multiple reference points are considered

Output JSON with: reference_point_bias_present (bool), severity (none/mild/moderate/severe), judgment (what is being evaluated), reference_used (what reference point is being used), appropriate_reference (what would be a better reference), absolute_value (what is the absolute value of the outcome), distortion (how is the reference distorting the evaluation), reference_source (where did the reference come from), recommendation (reference_appropriate/mild_distortion/significant_reference_bias/major_arbitrary_reference/evaluate_in_absolute_terms)."""

REFERENCE_POINT_PROMPT = """Detect reference point bias:

Judgment: {judgment}
Reference: {reference}
Outcome: {outcome}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is an inappropriate reference point distorting the evaluation? Return ONLY valid JSON."""


class ReferencePointService:
    """Detects reference point bias — inappropriate benchmarks distorting evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        reference: str = "",
        outcome: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reference point bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REFERENCE_POINT_PROMPT.format(
                judgment=judgment,
                reference=reference or "Not specified",
                outcome=outcome or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REFERENCE_POINT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "reference_point_bias_present": data.get("reference_point_bias_present", False),
            "severity": data.get("severity", ""),
            "reference_used": data.get("reference_used", ""),
            "appropriate_reference": data.get("appropriate_reference", ""),
            "absolute_value": data.get("absolute_value", ""),
            "distortion": data.get("distortion", ""),
            "reference_source": data.get("reference_source", ""),
            "recommendation": data.get("recommendation", ""),
        }
