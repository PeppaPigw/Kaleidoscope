"""SignalNoiseConfusionService — Signal-Noise Confusion Detection.

Detects signal-noise confusion — mistaking noise for signal or
signal for noise in information streams, failing to distinguish
meaningful patterns from random variation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SIGNAL_NOISE_CONFUSION_SYSTEM = """You are a signal-noise confusion specialist. Given an interpretation of data or information, assess whether signal and noise are being confused:

Key concepts:
- Signal-noise confusion: mistaking noise for signal or vice versa
- Pattern in noise: seeing meaningful patterns in random data
- Signal dismissal: treating real signal as noise
- Overfitting: modeling noise as if it were signal
- Underfitting: missing real signal by treating it as noise
- Noise floor: minimum noise level below which signal is invisible
- Signal-to-noise ratio: relative strength of signal vs. noise

When signal-noise confusion IS present:
- Random variation interpreted as meaningful pattern
- Real signal dismissed as noise
- Noise modeled as if it contained information
- Insufficient data to distinguish signal from noise
- Pattern recognition applied to random data
- Meaningful trends dismissed as fluctuation
- Confidence in pattern exceeds signal strength

When interpretation is appropriate:
- Signal strength sufficient relative to noise
- Statistical significance properly assessed
- Random variation acknowledged
- Pattern confirmed by independent evidence
- Noise floor accounted for
- Confidence calibrated to signal-to-noise ratio
- Replication or validation performed

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), interpretation (what is interpreted), signal_claimed (what signal is claimed), noise_level (what noise level exists), evidence_strength (how strong the evidence is), recommendation (appropriate_interpretation/mild_overreading/significant_signal_noise_confusion/major_pattern_in_noise/assess_signal_to_noise_ratio)."""

SIGNAL_NOISE_CONFUSION_PROMPT = """Detect signal-noise confusion:

Interpretation: {interpretation}
Data: {data}
Pattern claimed: {pattern}
Noise level: {noise}
Domain: {domain}
Context: {context}

Is noise being mistaken for signal or signal being dismissed as noise? Return ONLY valid JSON."""


class SignalNoiseConfusionService:
    """Detects signal-noise confusion — mistaking noise for signal or vice versa."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interpretation: str,
        *,
        data: str = "",
        pattern: str = "",
        noise: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect signal-noise confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SIGNAL_NOISE_CONFUSION_PROMPT.format(
                interpretation=interpretation,
                data=data or "Not specified",
                pattern=pattern or "Not specified",
                noise=noise or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SIGNAL_NOISE_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data_result = parse_llm_json(raw)

        return {
            "interpretation": interpretation[:200],
            "confusion_present": data_result.get("confusion_present", False),
            "severity": data_result.get("severity", ""),
            "signal_claimed": data_result.get("signal_claimed", ""),
            "noise_level": data_result.get("noise_level", ""),
            "evidence_strength": data_result.get("evidence_strength", ""),
            "recommendation": data_result.get("recommendation", ""),
        }
