"""QuantificationBiasService — Quantification Bias Detection.

Detects quantification bias — overvaluing what can be measured
and ignoring what cannot, leading to decisions based on incomplete
but precise information rather than complete but qualitative understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

QUANTIFICATION_BIAS_SYSTEM = """You are a quantification bias specialist. Given a decision or analysis, assess whether quantifiable factors are being overweighted relative to important but unquantifiable ones:

Key concepts:
- McNamara fallacy: making decisions based only on quantitative data
- Streetlight effect: looking where measurement is easy, not where answer is
- Metric fixation: over-reliance on numbers at expense of judgment
- Qualitative blindness: ignoring important factors because they can't be numbered
- False precision: precise numbers creating illusion of understanding
- Measurability bias: assuming measurable = important
- Intangible neglect: ignoring culture, morale, trust because unmeasurable

When quantification bias IS present:
- Decisions based only on measurable factors
- Important qualitative factors ignored or dismissed
- Precision confused with importance
- Unmeasurable factors treated as unimportant
- Numbers given authority over judgment
- Qualitative evidence dismissed as "anecdotal"
- Analysis limited to what can be quantified

When quantification is balanced:
- Both quantitative and qualitative factors considered
- Unmeasurable factors explicitly acknowledged
- Precision appropriate to actual knowledge
- Qualitative judgment valued alongside numbers
- Limitations of quantification acknowledged
- Important intangibles given weight in decisions
- Numbers inform but don't replace judgment

Output JSON with: bias_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), quantified (what factors are measured), neglected (what important factors are unmeasured), imbalance (how quantified factors dominate), recommendation (balanced_approach/mild_metric_preference/significant_qualitative_neglect/major_mcnamara_fallacy/include_qualitative_factors)."""

QUANTIFICATION_BIAS_PROMPT = """Detect quantification bias:

Decision: {decision}
Quantified factors: {quantified}
Qualitative factors: {qualitative}
Weighting: {weighting}
Domain: {domain}
Context: {context}

Are quantifiable factors being overvalued relative to important unquantifiable ones? Return ONLY valid JSON."""


class QuantificationBiasService:
    """Detects quantification bias — overvaluing measurable, ignoring unmeasurable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        quantified: str = "",
        qualitative: str = "",
        weighting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect quantification bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=QUANTIFICATION_BIAS_PROMPT.format(
                decision=decision,
                quantified=quantified or "Not specified",
                qualitative=qualitative or "Not specified",
                weighting=weighting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=QUANTIFICATION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "bias_present": data.get("bias_present", False),
            "severity": data.get("severity", ""),
            "quantified": data.get("quantified", ""),
            "neglected": data.get("neglected", ""),
            "imbalance": data.get("imbalance", ""),
            "recommendation": data.get("recommendation", ""),
        }
