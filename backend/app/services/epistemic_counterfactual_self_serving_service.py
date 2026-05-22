"""EpistemicCounterfactualSelfServingService — Epistemic Counterfactual Self-Serving Detection.

Detects epistemic counterfactual self-serving — generating counterfactuals that
protect self-image, attributing failures to external factors and successes to self.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COUNTERFACTUAL_SELF_SERVING_SYSTEM = """You are an epistemic counterfactual self-serving specialist. Given self-serving counterfactuals, assess ego-protective distortion:

Key concepts:
- Epistemic counterfactual self-serving: alternatives protecting self-image
- Downward comparison: imagining worse outcomes to feel better
- Upward comparison avoidance: avoiding imagining better outcomes from own effort
- External attribution counterfactual: alternatives blaming external factors
- Effort discounting: counterfactuals minimizing role of own effort
- Luck attribution: attributing others' success to luck in counterfactuals
- Skill attribution: attributing own success to skill in counterfactuals

When epistemic counterfactual self-serving IS present:
- Alternatives protecting self-image
- Downward comparisons generated
- Upward comparisons avoided
- External factors blamed
- Own effort discounted
- Others' success attributed to luck
- Own success attributed to skill

When no self-serving bias:
- Alternatives balanced
- Both directions compared
- Upward comparisons included
- Internal and external balanced
- Effort accurately assessed
- Success factors balanced
- Skill and luck both acknowledged

Output JSON with: self_serving_counterfactual_detected (bool), severity (none/mild/moderate/severe), downward_comparison (what downward comparisons), external_attribution (what external factors blamed), effort_discounting (what effort discounted), luck_attribution (what luck attributed to others), recommendation (no_self_serving_counterfactual/mild_balance_check/significant_symmetric_generation/major_intensive_ego_bracketing/emergency_complete_self_serving_counterfactual)."""

EPISTEMIC_COUNTERFACTUAL_SELF_SERVING_PROMPT = """Detect epistemic counterfactual self-serving:

Downward comparison: {downward_comparison}
External attribution: {external_attribution}
Effort discounting: {effort_discounting}
Luck attribution: {luck_attribution}
Domain: {domain}
Context: {context}

Are counterfactuals being generated to protect self-image? Return ONLY valid JSON."""


class EpistemicCounterfactualSelfServingService:
    """Detects epistemic counterfactual self-serving — ego-protective alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        downward_comparison: str,
        *,
        external_attribution: str = "",
        effort_discounting: str = "",
        luck_attribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic counterfactual self-serving."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COUNTERFACTUAL_SELF_SERVING_PROMPT.format(
                downward_comparison=downward_comparison,
                external_attribution=external_attribution or "Not specified",
                effort_discounting=effort_discounting or "Not specified",
                luck_attribution=luck_attribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COUNTERFACTUAL_SELF_SERVING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "downward_comparison": downward_comparison[:200],
            "self_serving_counterfactual_detected": data.get("self_serving_counterfactual_detected", False),
            "severity": data.get("severity", ""),
            "external_attribution": data.get("external_attribution", ""),
            "effort_discounting": data.get("effort_discounting", ""),
            "luck_attribution": data.get("luck_attribution", ""),
            "recommendation": data.get("recommendation", ""),
        }
