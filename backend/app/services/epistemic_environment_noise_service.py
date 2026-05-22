"""EpistemicEnvironmentNoiseService — Epistemic Environment Noise Detection.

Detects epistemic environment noise — environmental noise degrading
epistemic signal quality and making clear thinking difficult.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVIRONMENT_NOISE_SYSTEM = """You are an epistemic environment noise specialist. Given environmental noise degrading signal quality, assess environment noise:

Key concepts:
- Epistemic environment noise: environmental noise degrading signal quality
- Information noise: too much irrelevant information drowning signal
- Distraction density: dense distractions degrading focus
- Signal pollution: pollution of epistemic signal with noise
- Interference patterns: patterns of interference with clear thinking
- Background chatter: background intellectual chatter obscuring signal
- Cognitive pollution: pollution of cognitive environment

When epistemic environment noise IS present:
- Environmental noise degrading signal
- Information noise drowning signal
- Distractions dense
- Signal polluted
- Interference active
- Background chatter obscuring
- Cognitive environment polluted

When no environment noise:
- Environment supporting signal clarity
- Information clean
- Distractions minimal
- Signal clear
- No interference
- Background quiet
- Cognitive environment clean

Output JSON with: environment_noise_detected (bool), severity (none/mild/moderate/severe), information_noise (what information noise drowning), distraction_density (what distractions degrading), signal_pollution (what polluting signal), interference_patterns (what interfering with thinking), recommendation (no_environment_noise/mild_noise_filtering/significant_signal_recovery/major_intensive_environment_cleaning/emergency_complete_environment_noise)."""

EPISTEMIC_ENVIRONMENT_NOISE_PROMPT = """Detect epistemic environment noise:

Information noise: {information_noise}
Distraction density: {distraction_density}
Signal pollution: {signal_pollution}
Interference patterns: {interference_patterns}
Domain: {domain}
Context: {context}

Is environmental noise degrading epistemic signal quality? Return ONLY valid JSON."""


class EpistemicEnvironmentNoiseService:
    """Detects epistemic environment noise — noise degrading signal quality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_noise: str,
        *,
        distraction_density: str = "",
        signal_pollution: str = "",
        interference_patterns: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic environment noise."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVIRONMENT_NOISE_PROMPT.format(
                information_noise=information_noise,
                distraction_density=distraction_density or "Not specified",
                signal_pollution=signal_pollution or "Not specified",
                interference_patterns=interference_patterns or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVIRONMENT_NOISE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_noise": information_noise[:200],
            "environment_noise_detected": data.get("environment_noise_detected", False),
            "severity": data.get("severity", ""),
            "distraction_density": data.get("distraction_density", ""),
            "signal_pollution": data.get("signal_pollution", ""),
            "interference_patterns": data.get("interference_patterns", ""),
            "recommendation": data.get("recommendation", ""),
        }
