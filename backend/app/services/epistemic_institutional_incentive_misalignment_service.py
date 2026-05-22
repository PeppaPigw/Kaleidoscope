"""EpistemicInstitutionalIncentiveMisalignmentService — Epistemic Institutional Incentive Misalignment Detection.

Detects epistemic institutional incentive misalignment — institutional incentives
misaligned with truth-seeking, rewarding quantity over quality or novelty over accuracy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_INCENTIVE_MISALIGNMENT_SYSTEM = """You are an epistemic institutional incentive misalignment specialist. Given incentive misalignment, assess truth-seeking distortion:

Key concepts:
- Epistemic incentive misalignment: institutional incentives opposing truth-seeking
- Novelty bias: rewarding novel findings over replication
- Positive result bias: rewarding positive results over null findings
- Quantity over quality: rewarding publication count over rigor
- Career incentive distortion: career advancement misaligned with accuracy
- Metric gaming: gaming metrics rather than pursuing knowledge
- Short-term incentives: short-term rewards undermining long-term knowledge

When epistemic incentive misalignment IS present:
- Incentives opposing truth-seeking
- Novelty rewarded over replication
- Positive results rewarded over null
- Quantity over quality
- Career advancement misaligned
- Metrics gamed
- Short-term rewards dominating

When no incentive misalignment:
- Incentives aligned with truth-seeking
- Replication valued
- Null results published
- Quality prioritized
- Career rewards accuracy
- Metrics meaningful
- Long-term knowledge valued

Output JSON with: incentive_misalignment_detected (bool), severity (none/mild/moderate/severe), novelty_bias (what novelty bias), positive_result_bias (what positive result bias), quantity_over_quality (what quantity over quality), metric_gaming (what metrics gamed), recommendation (no_incentive_misalignment/mild_incentive_awareness/significant_incentive_reform/major_intensive_realignment/emergency_complete_incentive_misalignment)."""

EPISTEMIC_INSTITUTIONAL_INCENTIVE_MISALIGNMENT_PROMPT = """Detect epistemic institutional incentive misalignment:

Novelty bias: {novelty_bias}
Positive result bias: {positive_result_bias}
Quantity over quality: {quantity_over_quality}
Metric gaming: {metric_gaming}
Domain: {domain}
Context: {context}

Are institutional incentives misaligned with truth-seeking? Return ONLY valid JSON."""


class EpistemicInstitutionalIncentiveMisalignmentService:
    """Detects epistemic incentive misalignment — truth-seeking distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        novelty_bias: str,
        *,
        positive_result_bias: str = "",
        quantity_over_quality: str = "",
        metric_gaming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional incentive misalignment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_INCENTIVE_MISALIGNMENT_PROMPT.format(
                novelty_bias=novelty_bias,
                positive_result_bias=positive_result_bias or "Not specified",
                quantity_over_quality=quantity_over_quality or "Not specified",
                metric_gaming=metric_gaming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_INCENTIVE_MISALIGNMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "novelty_bias": novelty_bias[:200],
            "incentive_misalignment_detected": data.get("incentive_misalignment_detected", False),
            "severity": data.get("severity", ""),
            "positive_result_bias": data.get("positive_result_bias", ""),
            "quantity_over_quality": data.get("quantity_over_quality", ""),
            "metric_gaming": data.get("metric_gaming", ""),
            "recommendation": data.get("recommendation", ""),
        }
