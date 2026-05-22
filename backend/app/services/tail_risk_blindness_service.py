"""TailRiskBlindnessService — Tail Risk Blindness Detection.

Detects tail risk blindness — ignoring low-probability high-impact
events, treating thin-tailed distributions as if they apply to
fat-tailed domains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TAIL_RISK_BLINDNESS_SYSTEM = """You are a tail risk blindness specialist. Given a risk assessment, evaluate whether tail risks are being ignored:

Key concepts:
- Tail risk: low-probability, high-impact events
- Fat tails: distributions with more extreme events than normal
- Black swan: unpredicted extreme events
- Expected value vs ruin: average outcomes vs catastrophic ones
- Ergodicity: whether time averages equal ensemble averages
- Fragility: vulnerability to extreme events
- Precautionary principle: asymmetric response to tail risks

When tail risk blindness IS present:
- Low-probability high-impact events ignored
- Normal distribution assumed in fat-tailed domain
- Expected value used when ruin is possible
- Historical data assumed to capture all possibilities
- Extreme events dismissed as "unlikely"
- No preparation for catastrophic scenarios
- Risk assessment truncates at convenient boundary

When tail risks are recognized:
- Extreme events explicitly considered
- Fat-tailed distributions used where appropriate
- Ruin scenarios given special weight
- Precautionary principle applied to catastrophic risks
- Historical data not assumed to be complete
- Fragility to extremes assessed
- Asymmetric response to downside tail risks

Output JSON with: blindness_present (bool), severity (none/mild/moderate/severe), assessment (what risk is assessed), tail_ignored (what extreme events are dismissed), distribution_assumed (what distribution is used), actual_distribution (what distribution likely applies), recommendation (tail_risks_recognized/mild_underweighting/significant_blindness/major_tail_risk_ignored/assess_extreme_scenarios)."""

TAIL_RISK_BLINDNESS_PROMPT = """Detect tail risk blindness:

Assessment: {assessment}
Risks considered: {risks}
Extreme scenarios: {extremes}
Distribution assumed: {distribution}
Domain: {domain}
Context: {context}

Are low-probability high-impact events being ignored? Return ONLY valid JSON."""


class TailRiskBlindnessService:
    """Detects tail risk blindness — ignoring low-probability high-impact events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        risks: str = "",
        extremes: str = "",
        distribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tail risk blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TAIL_RISK_BLINDNESS_PROMPT.format(
                assessment=assessment,
                risks=risks or "Not specified",
                extremes=extremes or "Not specified",
                distribution=distribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TAIL_RISK_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "blindness_present": data.get("blindness_present", False),
            "severity": data.get("severity", ""),
            "tail_ignored": data.get("tail_ignored", ""),
            "distribution_assumed": data.get("distribution_assumed", ""),
            "actual_distribution": data.get("actual_distribution", ""),
            "recommendation": data.get("recommendation", ""),
        }
