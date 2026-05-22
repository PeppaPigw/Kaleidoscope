"""EpistemicTemporalExtensionFallacyService — Epistemic Temporal Extension Fallacy Detection.

Detects epistemic temporal extension fallacy — extending short-term patterns
into permanent states, assuming current trends continue indefinitely.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_EXTENSION_FALLACY_SYSTEM = """You are an epistemic temporal extension fallacy specialist. Given short-term patterns extended indefinitely, assess temporal extension:

Key concepts:
- Epistemic temporal extension: extending short-term patterns into permanent states
- Trend extrapolation: assuming current trends continue forever
- Permanence assumption: assuming current state is permanent
- Mean reversion blindness: missing tendency to revert to mean
- Regime change blindness: missing potential for regime changes
- Saturation blindness: missing saturation points and limits
- Phase transition ignorance: ignoring potential phase transitions

When epistemic temporal extension IS present:
- Short-term extended indefinitely
- Trends extrapolated without limit
- Current state assumed permanent
- Mean reversion missed
- Regime changes ignored
- Saturation points missed
- Phase transitions ignored

When no temporal extension:
- Short-term bounded appropriately
- Trends qualified with limits
- Impermanence acknowledged
- Mean reversion considered
- Regime changes anticipated
- Saturation points identified
- Phase transitions considered

Output JSON with: temporal_extension_detected (bool), severity (none/mild/moderate/severe), trend_extrapolation (what trends extrapolated), permanence_assumption (what assumed permanent), mean_reversion_blindness (what mean reversion missed), regime_change_blindness (what regime changes ignored), recommendation (no_temporal_extension/mild_boundary_awareness/significant_limit_identification/major_intensive_temporal_bounding/emergency_complete_temporal_extension)."""

EPISTEMIC_TEMPORAL_EXTENSION_FALLACY_PROMPT = """Detect epistemic temporal extension fallacy:

Trend extrapolation: {trend_extrapolation}
Permanence assumption: {permanence_assumption}
Mean reversion blindness: {mean_reversion_blindness}
Regime change blindness: {regime_change_blindness}
Domain: {domain}
Context: {context}

Are short-term patterns being extended into permanent states? Return ONLY valid JSON."""


class EpistemicTemporalExtensionFallacyService:
    """Detects epistemic temporal extension — short-term as permanent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        trend_extrapolation: str,
        *,
        permanence_assumption: str = "",
        mean_reversion_blindness: str = "",
        regime_change_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal extension fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_EXTENSION_FALLACY_PROMPT.format(
                trend_extrapolation=trend_extrapolation,
                permanence_assumption=permanence_assumption or "Not specified",
                mean_reversion_blindness=mean_reversion_blindness or "Not specified",
                regime_change_blindness=regime_change_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_EXTENSION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trend_extrapolation": trend_extrapolation[:200],
            "temporal_extension_detected": data.get("temporal_extension_detected", False),
            "severity": data.get("severity", ""),
            "permanence_assumption": data.get("permanence_assumption", ""),
            "mean_reversion_blindness": data.get("mean_reversion_blindness", ""),
            "regime_change_blindness": data.get("regime_change_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
