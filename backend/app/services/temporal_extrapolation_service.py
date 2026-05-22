"""TemporalExtrapolationService — Trend Extrapolation Validity Assessment.

Takes a trend and assesses whether extrapolating it is justified.
Identifies what could break the trend, distinguishes linear from
exponential from S-curve dynamics, and flags naive extrapolation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXTRAPOLATION_SYSTEM = """You are a trend extrapolation analyst. Given a trend, assess whether extrapolation is justified:
- What's the underlying dynamic? (linear/exponential/logistic_S_curve/power_law/cyclical)
- What mechanism drives the trend? (is it sustainable?)
- What could break the trend? (saturation, resource limits, regime changes)
- Historical base rate: how often do trends of this type continue vs break?
- What's the appropriate extrapolation horizon?

Output JSON with: trend_type (linear/exponential/logistic/power_law/cyclical/unknown), mechanism (what drives it), mechanism_sustainable (bool), extrapolation_justified (bool), safe_horizon (how far you can reasonably extrapolate), break_factors (list of: factor, likelihood (0-1), when_it_bites), historical_base_rate (how often similar trends continued), naive_extrapolation_error (what you'd get wrong by just extending the line), better_model (what model fits better than naive extrapolation), confidence_bounds (how wide should error bars be), regime_change_risk (0-1, probability the underlying dynamic changes)."""

EXTRAPOLATION_PROMPT = """Assess this trend extrapolation:

Trend: {trend}
Data period: {period}
Extrapolation target: {target}
Domain: {domain}

Is extrapolation justified? Return ONLY valid JSON."""


class TemporalExtrapolationService:
    """Assesses whether trend extrapolation is justified."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        trend: str,
        *,
        period: str = "",
        target: str = "",
        domain: str = "",
    ) -> dict:
        """Assess whether extrapolating a trend is justified."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXTRAPOLATION_PROMPT.format(
                trend=trend,
                period=period or "Not specified",
                target=target or "Next 5-10 years",
                domain=domain or "general",
            ),
            system=EXTRAPOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trend": trend[:200],
            "trend_type": data.get("trend_type", ""),
            "mechanism": data.get("mechanism", ""),
            "mechanism_sustainable": data.get("mechanism_sustainable", False),
            "extrapolation_justified": data.get("extrapolation_justified", False),
            "safe_horizon": data.get("safe_horizon", ""),
            "break_factors": data.get("break_factors", []),
            "historical_base_rate": data.get("historical_base_rate", ""),
            "naive_extrapolation_error": data.get("naive_extrapolation_error", ""),
            "better_model": data.get("better_model", ""),
            "regime_change_risk": data.get("regime_change_risk", 0),
        }
