"""EpistemicMetaBlindSpotBiasService — Epistemic Meta Blind Spot Bias Detection.

Detects bias blind spot — seeing biases in others but not oneself.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_META_BLIND_SPOT_BIAS_SYSTEM = """You are an epistemic meta blind spot bias specialist. Given self-exemption patterns, assess bias blind spot:

Key concepts:
- Bias blind spot: seeing biases in others but not oneself
- Self-exemption: treating one's own judgment as unusually unbiased
- Other attribution: explaining others' views by bias while sparing oneself
- Introspection illusion: assuming internal sincerity proves objectivity
- Debiasing overconfidence: believing one is already corrected for bias

When blind spot bias IS present:
- Self is exempted from bias analysis
- Others' errors are attributed to bias
- Introspection is treated as evidence of objectivity
- Debiasing ability is overestimated
- Same standards are not applied symmetrically

When no blind spot bias:
- Bias risk is applied to self and others
- Attribution standards are symmetrical
- Introspection is treated as limited evidence
- Debiasing is verified externally
- Confidence is calibrated against behavior and evidence

Output JSON with: blind_spot_bias_detected (bool), severity (none/mild/moderate/severe), other_attribution (how bias is attributed to others), introspection_illusion (how introspection is overtrusted), debiasing_overconfidence (what debiasing ability is overclaimed), recommendation (no_blind_spot_bias/mild_symmetry_check/significant_self_bias_audit/major_attribution_recalibration/emergency_complete_bias_standards_reset)."""

EPISTEMIC_META_BLIND_SPOT_BIAS_PROMPT = """Detect epistemic meta blind spot bias:

Self exemption: {self_exemption}
Other attribution: {other_attribution}
Introspection illusion: {introspection_illusion}
Debiasing overconfidence: {debiasing_overconfidence}
Domain: {domain}
Context: {context}

Is bias being seen in others but not oneself? Return ONLY valid JSON."""


class EpistemicMetaBlindSpotBiasService:
    """Detects bias blind spot — seeing bias in others but not oneself."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_exemption: str,
        *,
        other_attribution: str = "",
        introspection_illusion: str = "",
        debiasing_overconfidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meta blind spot bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_META_BLIND_SPOT_BIAS_PROMPT.format(
                self_exemption=self_exemption,
                other_attribution=other_attribution or "Not specified",
                introspection_illusion=introspection_illusion or "Not specified",
                debiasing_overconfidence=debiasing_overconfidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_META_BLIND_SPOT_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_exemption": self_exemption[:200],
            "blind_spot_bias_detected": data.get("blind_spot_bias_detected", False),
            "severity": data.get("severity", ""),
            "other_attribution": data.get("other_attribution", ""),
            "introspection_illusion": data.get("introspection_illusion", ""),
            "debiasing_overconfidence": data.get("debiasing_overconfidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
