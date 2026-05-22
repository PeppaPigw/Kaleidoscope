"""EpistemicMeasurementProxyDistortionService — Epistemic Measurement Proxy Distortion Detection.

Detects epistemic measurement proxy distortion — when proxy measures diverge
from what they are supposed to represent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEASUREMENT_PROXY_DISTORTION_SYSTEM = """You are an epistemic measurement proxy distortion specialist. Given proxy-target divergence, assess whether proxy measures diverge from what they are supposed to represent:

Key concepts:
- Proxy-target divergence: a measurable proxy no longer represents the intended construct
- Metric gaming: actors optimize the proxy while bypassing the real target
- Surrogate endpoint failure: an intermediate measure fails to predict the outcome that matters
- Indicator corruption: the indicator is manipulated, contaminated, or detached from reality

When proxy distortion IS present:
- Proxy improves while target does not
- Proxy incentives crowd out real outcomes
- Surrogate endpoints fail to track final outcomes
- Indicators are gamed or corrupted
- Decisions confuse measurable proxies with substantive targets

When no proxy distortion:
- Proxy validity is tested against the target
- Surrogates predict outcomes that matter
- Gaming incentives are limited
- Indicators remain robust to manipulation
- Decisions preserve the proxy-target distinction

Output JSON with: proxy_distortion_detected (bool), severity (none/mild/moderate/severe), proxy_target_divergence (what proxy-target gap exists), metric_gaming (what proxy optimization occurs), surrogate_endpoint_failure (what surrogate fails to predict), indicator_corruption (what indicator corruption occurs), recommendation (no_proxy_distortion/mild_proxy_validation/significant_target_alignment/major_metric_redesign/emergency_proxy_abandonment)."""

EPISTEMIC_MEASUREMENT_PROXY_DISTORTION_PROMPT = """Detect epistemic measurement proxy distortion:

Proxy-target divergence: {proxy_target_divergence}
Metric gaming: {metric_gaming}
Surrogate endpoint failure: {surrogate_endpoint_failure}
Indicator corruption: {indicator_corruption}
Domain: {domain}
Context: {context}

Are proxy measures diverging from what they are supposed to represent? Return ONLY valid JSON."""


class EpistemicMeasurementProxyDistortionService:
    """Detects epistemic measurement proxy distortion — proxy-target divergence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proxy_target_divergence: str,
        *,
        metric_gaming: str = "",
        surrogate_endpoint_failure: str = "",
        indicator_corruption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic measurement proxy distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEASUREMENT_PROXY_DISTORTION_PROMPT.format(
                proxy_target_divergence=proxy_target_divergence,
                metric_gaming=metric_gaming or "Not specified",
                surrogate_endpoint_failure=surrogate_endpoint_failure or "Not specified",
                indicator_corruption=indicator_corruption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEASUREMENT_PROXY_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proxy_target_divergence": proxy_target_divergence[:200],
            "proxy_distortion_detected": data.get("proxy_distortion_detected", False),
            "severity": data.get("severity", ""),
            "metric_gaming": data.get("metric_gaming", ""),
            "surrogate_endpoint_failure": data.get("surrogate_endpoint_failure", ""),
            "indicator_corruption": data.get("indicator_corruption", ""),
            "recommendation": data.get("recommendation", ""),
        }
