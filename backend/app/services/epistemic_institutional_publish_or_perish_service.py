"""EpistemicInstitutionalPublishOrPerishService — Epistemic Institutional Publish or Perish Detection.

Detects epistemic institutional publish or perish — publish-or-perish
distortions in knowledge production.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_PUBLISH_OR_PERISH_SYSTEM = """You are an epistemic institutional publish or perish specialist. Given quantity pressure, assess knowledge production distortion:

Key concepts:
- Epistemic publish or perish: publication quantity pressure distorting knowledge production
- Quantity over quality: publication count prioritized over rigor and importance
- Salami slicing: splitting findings into minimum publishable units
- Novelty bias in publishing: novel claims favored over careful confirmation
- Replication disincentive: replication work undervalued or penalized

When epistemic publish or perish IS present:
- Quantity prioritized over quality
- Findings salami sliced
- Novelty bias shapes publication choices
- Replication disincentivized
- Research value measured by output count

When no publish or perish distortion:
- Quality prioritized over quantity
- Findings published whole
- Novelty balanced with rigor
- Replication valued
- Research value measured by contribution

Output JSON with: publish_or_perish_detected (bool), severity (none/mild/moderate/severe), salami_slicing (what salami slicing), novelty_bias_in_publishing (what novelty bias in publishing), replication_disincentive (what replication disincentive), recommendation (no_publish_perish/mild_quality_emphasis/significant_publication_reform/major_intensive_incentive_reform/emergency_complete_publish_perish)."""

EPISTEMIC_INSTITUTIONAL_PUBLISH_OR_PERISH_PROMPT = """Detect epistemic institutional publish or perish:

Quantity over quality: {quantity_over_quality}
Salami slicing: {salami_slicing}
Novelty bias in publishing: {novelty_bias_in_publishing}
Replication disincentive: {replication_disincentive}
Domain: {domain}
Context: {context}

Is publish-or-perish pressure distorting knowledge production? Return ONLY valid JSON."""


class EpistemicInstitutionalPublishOrPerishService:
    """Detects epistemic publish or perish — quality distortion from pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        quantity_over_quality: str,
        *,
        salami_slicing: str = "",
        novelty_bias_in_publishing: str = "",
        replication_disincentive: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional publish or perish."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_PUBLISH_OR_PERISH_PROMPT.format(
                quantity_over_quality=quantity_over_quality,
                salami_slicing=salami_slicing or "Not specified",
                novelty_bias_in_publishing=novelty_bias_in_publishing or "Not specified",
                replication_disincentive=replication_disincentive or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_PUBLISH_OR_PERISH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "quantity_over_quality": quantity_over_quality[:200],
            "publish_or_perish_detected": data.get("publish_or_perish_detected", False),
            "severity": data.get("severity", ""),
            "salami_slicing": data.get("salami_slicing", ""),
            "novelty_bias_in_publishing": data.get("novelty_bias_in_publishing", ""),
            "replication_disincentive": data.get("replication_disincentive", ""),
            "recommendation": data.get("recommendation", ""),
        }
