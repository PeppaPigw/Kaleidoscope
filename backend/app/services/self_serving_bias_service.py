"""SelfServingBiasService — Self-Serving Bias Detection.

Detects self-serving bias — attributing successes to internal
factors (skill, effort) and failures to external factors (luck,
circumstances, others). Miller & Ross (1975). "I succeeded
because I'm talented; I failed because the system is unfair."
Protects self-esteem but prevents learning from failure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELF_SERVING_SYSTEM = """You are a self-serving bias specialist. Given an attribution for success or failure, assess whether the attribution pattern is self-serving rather than accurate:

Key concepts (Miller & Ross, 1975):
- Self-serving bias: internal attribution for success, external for failure
- Self-enhancement: taking credit for good outcomes
- Self-protection: deflecting blame for bad outcomes
- Fundamental attribution error overlap: but self-serving is specifically about self vs. others
- Actor-observer asymmetry: we explain our own behavior differently than others'
- Defensive attribution: protecting self-esteem through biased causal reasoning

When self-serving bias IS present:
- Taking full credit for team successes
- Blaming circumstances, others, or luck for personal failures
- "I earned this" for success but "it wasn't my fault" for failure
- Asymmetric attribution pattern across successes and failures
- Inability to identify personal contribution to failures
- Overestimating personal role in successes

When the attribution IS accurate:
- External factors genuinely caused the failure (documented, verifiable)
- Internal factors genuinely caused the success (skill clearly demonstrated)
- The person acknowledges both internal and external factors
- The attribution pattern is consistent (not asymmetric)
- Others confirm the attribution independently

Output JSON with: self_serving_present (bool), severity (none/mild/moderate/severe), outcome (success or failure being attributed), attribution (how the outcome is being explained), internal_factors (personal factors cited), external_factors (external factors cited), attribution_asymmetry (bool — different patterns for success vs failure?), self_enhancement (bool — taking excess credit for success?), self_protection (bool — deflecting blame for failure?), evidence_for_attribution (what supports the given attribution?), evidence_against (what contradicts it?), learning_blocked (bool — is the bias preventing learning?), pattern_consistency (is the attribution pattern consistent across outcomes?), recommendation (attribution_accurate/mild_self_serving/significant_asymmetry/major_self_serving_bias/examine_own_contribution)."""

SELF_SERVING_PROMPT = """Detect self-serving bias:

Outcome: {outcome}
Attribution: {attribution}
Success pattern: {success_pattern}
Failure pattern: {failure_pattern}
Domain: {domain}
Context: {context}

Is the attribution pattern self-serving rather than accurate? Return ONLY valid JSON."""


class SelfServingBiasService:
    """Detects self-serving bias — asymmetric attribution for success vs failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        outcome: str,
        *,
        attribution: str = "",
        success_pattern: str = "",
        failure_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect self-serving bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELF_SERVING_PROMPT.format(
                outcome=outcome,
                attribution=attribution or "Not specified",
                success_pattern=success_pattern or "Not specified",
                failure_pattern=failure_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELF_SERVING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "outcome": outcome[:200],
            "self_serving_present": data.get("self_serving_present", False),
            "severity": data.get("severity", ""),
            "attribution": data.get("attribution", ""),
            "internal_factors": data.get("internal_factors", ""),
            "external_factors": data.get("external_factors", ""),
            "attribution_asymmetry": data.get("attribution_asymmetry", False),
            "self_enhancement": data.get("self_enhancement", False),
            "self_protection": data.get("self_protection", False),
            "evidence_for_attribution": data.get("evidence_for_attribution", ""),
            "evidence_against": data.get("evidence_against", ""),
            "learning_blocked": data.get("learning_blocked", False),
            "pattern_consistency": data.get("pattern_consistency", ""),
            "recommendation": data.get("recommendation", ""),
        }
