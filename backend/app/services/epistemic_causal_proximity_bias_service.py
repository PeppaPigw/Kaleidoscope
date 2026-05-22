"""EpistemicCausalProximityBiasService — Epistemic Causal Proximity Bias Detection.

Detects epistemic causal proximity bias — favoring proximate causes
over distal ones, missing deeper structural causes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_PROXIMITY_BIAS_SYSTEM = """You are an epistemic causal proximity bias specialist. Given favoring proximate over distal causes, assess proximity bias:

Key concepts:
- Epistemic causal proximity bias: favoring proximate causes over distal ones
- Recency preference: preferring recent causes over historical ones
- Visibility bias: preferring visible causes over hidden structural ones
- Individual attribution: attributing to individuals rather than systems
- Trigger fixation: fixating on trigger rather than underlying conditions
- Surface cause preference: preferring surface causes over deep ones
- Immediate over structural: preferring immediate over structural explanations

When epistemic causal proximity bias IS present:
- Proximate causes favored
- Recent causes preferred
- Visible causes preferred
- Individuals blamed over systems
- Triggers fixated on
- Surface causes preferred
- Immediate over structural

When no proximity bias:
- Proximate and distal balanced
- Historical causes considered
- Hidden causes sought
- Systems and individuals both considered
- Underlying conditions examined
- Deep causes explored
- Structural explanations considered

Output JSON with: causal_proximity_bias_detected (bool), severity (none/mild/moderate/severe), recency_preference (what recent causes preferred), visibility_bias (what visible causes preferred), individual_attribution (what individuals blamed), trigger_fixation (what triggers fixated on), recommendation (no_proximity_bias/mild_distal_awareness/significant_structural_analysis/major_intensive_deep_cause_pursuit/emergency_complete_proximity_bias)."""

EPISTEMIC_CAUSAL_PROXIMITY_BIAS_PROMPT = """Detect epistemic causal proximity bias:

Recency preference: {recency_preference}
Visibility bias: {visibility_bias}
Individual attribution: {individual_attribution}
Trigger fixation: {trigger_fixation}
Domain: {domain}
Context: {context}

Are proximate causes being favored over distal structural ones? Return ONLY valid JSON."""


class EpistemicCausalProximityBiasService:
    """Detects epistemic causal proximity bias — near over far causes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        recency_preference: str,
        *,
        visibility_bias: str = "",
        individual_attribution: str = "",
        trigger_fixation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic causal proximity bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_PROXIMITY_BIAS_PROMPT.format(
                recency_preference=recency_preference,
                visibility_bias=visibility_bias or "Not specified",
                individual_attribution=individual_attribution or "Not specified",
                trigger_fixation=trigger_fixation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_PROXIMITY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "recency_preference": recency_preference[:200],
            "causal_proximity_bias_detected": data.get("causal_proximity_bias_detected", False),
            "severity": data.get("severity", ""),
            "visibility_bias": data.get("visibility_bias", ""),
            "individual_attribution": data.get("individual_attribution", ""),
            "trigger_fixation": data.get("trigger_fixation", ""),
            "recommendation": data.get("recommendation", ""),
        }
