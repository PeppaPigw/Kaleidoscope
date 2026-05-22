"""OverconfidenceIntervalService — Overconfidence Interval Detection.

Detects overconfidence in interval estimates — tendency to
set confidence intervals that are too narrow, reflecting
excessive certainty about the range of possible outcomes.
Alpert & Raiffa (1982). When asked for 90% confidence
intervals, people typically capture only 50% of outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERCONFIDENCE_INTERVAL_SYSTEM = """You are an overconfidence interval specialist. Given a range estimate or confidence interval, assess whether the interval is too narrow:

Key concepts (Alpert & Raiffa, 1982):
- Interval overconfidence: confidence intervals too narrow
- Anchoring and insufficient adjustment: starting from point estimate
- 90% intervals capturing only 50%: systematic miscalibration
- Surprise index: how often outcomes fall outside stated intervals
- Thin-tailed thinking: underestimating probability of extreme outcomes
- Known unknowns vs unknown unknowns: intervals miss what's not considered
- Reference class forecasting: using historical ranges as calibration

When overconfidence interval IS present:
- "I'm 90% sure it's between X and Y" with too narrow a range
- Confidence intervals that don't account for uncertainty sources
- Ranges based on best-case/worst-case that aren't extreme enough
- Historical outcomes frequently falling outside stated ranges
- Not considering what could go wrong beyond the obvious
- Point estimates with tiny error bars on inherently uncertain quantities

When the interval IS appropriate:
- The range is based on well-calibrated historical data
- The person has demonstrated good interval calibration
- The uncertainty sources are well-understood and bounded
- The interval explicitly accounts for known unknowns
- Reference class data supports the stated range

Output JSON with: overconfidence_interval_present (bool), severity (none/mild/moderate/severe), estimate (what is being estimated), stated_interval (what interval is given), stated_confidence (what confidence level is claimed), likely_coverage (what coverage does the interval actually provide), too_narrow_by (how much wider should it be), uncertainty_sources (what sources of uncertainty exist), historical_calibration (how well calibrated historically), recommendation (interval_appropriate/mild_narrowness/significant_overconfidence/major_interval_overconfidence/widen_interval_significantly)."""

OVERCONFIDENCE_INTERVAL_PROMPT = """Detect overconfidence interval:

Estimate: {estimate}
Interval: {interval}
Confidence: {confidence}
Basis: {basis}
Domain: {domain}
Context: {context}

Is the confidence interval too narrow for the stated confidence level? Return ONLY valid JSON."""


class OverconfidenceIntervalService:
    """Detects overconfidence intervals — confidence ranges that are too narrow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        estimate: str,
        *,
        interval: str = "",
        confidence: str = "",
        basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect overconfidence interval."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERCONFIDENCE_INTERVAL_PROMPT.format(
                estimate=estimate,
                interval=interval or "Not specified",
                confidence=confidence or "Not specified",
                basis=basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OVERCONFIDENCE_INTERVAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "estimate": estimate[:200],
            "overconfidence_interval_present": data.get("overconfidence_interval_present", False),
            "severity": data.get("severity", ""),
            "stated_interval": data.get("stated_interval", ""),
            "stated_confidence": data.get("stated_confidence", ""),
            "likely_coverage": data.get("likely_coverage", ""),
            "too_narrow_by": data.get("too_narrow_by", ""),
            "uncertainty_sources": data.get("uncertainty_sources", ""),
            "historical_calibration": data.get("historical_calibration", ""),
            "recommendation": data.get("recommendation", ""),
        }
