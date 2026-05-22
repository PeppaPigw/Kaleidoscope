"""EpistemicCounterfactualAsymmetryService — Epistemic Counterfactual Asymmetry Detection.

Detects epistemic counterfactual asymmetry — only considering upward
or downward counterfactuals, creating systematic bias.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_ASYMMETRY_SYSTEM = """You are an epistemic counterfactual asymmetry specialist. Given asymmetric counterfactual thinking, assess counterfactual asymmetry:

Key concepts:
- Epistemic counterfactual asymmetry: only considering upward or downward counterfactuals
- Upward bias: only imagining how things could have been better
- Downward bias: only imagining how things could have been worse
- Gratitude-regret imbalance: systematic tilt toward regret or gratitude
- Selective imagination: imagining only in one direction
- Motivational distortion: asymmetry serving motivational rather than epistemic goals
- Comparison bias: systematically biased comparison set

When epistemic counterfactual asymmetry IS present:
- Only one direction considered
- Upward or downward bias present
- Gratitude-regret imbalanced
- Imagination selective
- Motivation distorting counterfactuals
- Comparison set biased
- Systematic tilt in one direction

When no counterfactual asymmetry:
- Both directions considered
- Upward and downward balanced
- Gratitude and regret proportionate
- Imagination balanced
- Counterfactuals epistemically motivated
- Comparison set fair
- No systematic tilt

Output JSON with: counterfactual_asymmetry_detected (bool), severity (none/mild/moderate/severe), upward_bias (what upward bias), downward_bias (what downward bias), selective_imagination (what selectively imagined), motivational_distortion (what motivation distorts), recommendation (no_counterfactual_asymmetry/mild_balance_practice/significant_direction_correction/major_intensive_symmetry_training/emergency_complete_counterfactual_asymmetry)."""

EPISTEMIC_COUNTERFACTUAL_ASYMMETRY_PROMPT = """Detect epistemic counterfactual asymmetry:

Upward bias: {upward_bias}
Downward bias: {downward_bias}
Selective imagination: {selective_imagination}
Motivational distortion: {motivational_distortion}
Domain: {domain}
Context: {context}

Is counterfactual thinking asymmetric — only one direction considered? Return ONLY valid JSON."""


class EpistemicCounterfactualAsymmetryService:
    """Detects epistemic counterfactual asymmetry — one-directional what-ifs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        upward_bias: str,
        *,
        downward_bias: str = "",
        selective_imagination: str = "",
        motivational_distortion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_ASYMMETRY_PROMPT.format(
                upward_bias=upward_bias,
                downward_bias=downward_bias or "Not specified",
                selective_imagination=selective_imagination or "Not specified",
                motivational_distortion=motivational_distortion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "upward_bias": upward_bias[:200],
            "counterfactual_asymmetry_detected": data.get("counterfactual_asymmetry_detected", False),
            "severity": data.get("severity", ""),
            "downward_bias": data.get("downward_bias", ""),
            "selective_imagination": data.get("selective_imagination", ""),
            "motivational_distortion": data.get("motivational_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
