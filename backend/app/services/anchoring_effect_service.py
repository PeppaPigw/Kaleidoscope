"""AnchoringEffectService — Anchoring Bias Detection.

Identifies when a judgment or estimate is being unduly influenced
by an initial piece of information (the anchor), even when that
anchor is arbitrary or irrelevant. Suggests debiasing strategies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ANCHORING_SYSTEM = """You are an anchoring bias specialist. Given a judgment or estimate, assess whether it's being anchored by an initial value:
- Is there an obvious anchor (first number mentioned, initial offer, status quo)?
- Would the judgment be different if the anchor were different?
- Is the anchor relevant or arbitrary?
- How strong is the anchoring effect likely to be?
- What debiasing strategies would help?

Output JSON with: anchor_present (bool), anchor_value (the anchoring information), anchor_source (where the anchor comes from), anchor_relevance (relevant/partially_relevant/irrelevant/arbitrary), anchoring_strength (0-1, how much the anchor is likely distorting judgment), adjustment_direction (too_high/too_low/unknown), likely_unanchored_estimate (what the estimate might be without the anchor), debiasing_strategies (list of: strategy, effectiveness (low/moderate/high)), consider_opposite (what you'd think if the anchor were very different), anchoring_type (numeric/status_quo/primacy/framing), vulnerability_factors (why this situation is especially susceptible to anchoring), recommendation (anchor_valid/partially_discount/fully_discount/reanchor)."""

ANCHORING_PROMPT = """Detect anchoring effects:

Judgment/Estimate: {judgment}
Context: {context}
Initial information: {initial_info}
Domain: {domain}

Is this judgment anchored? Return ONLY valid JSON."""


class AnchoringEffectService:
    """Detects anchoring bias in judgments and estimates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        initial_info: str = "",
        context: str = "",
        domain: str = "",
    ) -> dict:
        """Detect anchoring effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ANCHORING_PROMPT.format(
                judgment=judgment,
                initial_info=initial_info or "Not explicitly stated",
                context=context or "No additional context",
                domain=domain or "general",
            ),
            system=ANCHORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "anchor_present": data.get("anchor_present", False),
            "anchor_value": data.get("anchor_value", ""),
            "anchor_source": data.get("anchor_source", ""),
            "anchor_relevance": data.get("anchor_relevance", ""),
            "anchoring_strength": data.get("anchoring_strength", 0),
            "adjustment_direction": data.get("adjustment_direction", ""),
            "likely_unanchored_estimate": data.get("likely_unanchored_estimate", ""),
            "debiasing_strategies": data.get("debiasing_strategies", []),
            "consider_opposite": data.get("consider_opposite", ""),
            "anchoring_type": data.get("anchoring_type", ""),
            "vulnerability_factors": data.get("vulnerability_factors", ""),
            "recommendation": data.get("recommendation", ""),
        }
