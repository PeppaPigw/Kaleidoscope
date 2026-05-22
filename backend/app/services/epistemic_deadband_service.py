"""EpistemicDeadbandService — Epistemic Deadband Detection.

Detects epistemic deadband — a range of intellectual input where no
output change occurs, creating insensitivity zones in reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEADBAND_SYSTEM = """You are an epistemic deadband specialist. Given an intellectual response pattern, assess whether insensitivity zones exist:

Key concepts:
- Epistemic deadband: input range with no output change
- Threshold: minimum input to produce response
- Insensitivity: ignoring small changes
- Noise rejection: filtering out insignificant variation
- Resolution: smallest detectable change
- Quantization: discrete steps in response
- Saturation: maximum response regardless of input

When epistemic deadband IS present:
- Range of input where no output change occurs
- Minimum threshold before any response
- Small changes being ignored
- Insignificant variations filtered out
- Limited ability to detect small changes
- Discrete jumps rather than smooth response
- Maximum response ceiling reached

When full sensitivity is present:
- Every input change produces output change
- No minimum threshold
- All changes registered
- No filtering of variations
- Infinite resolution
- Smooth continuous response
- No saturation ceiling

Output JSON with: deadband_present (bool), severity (none/mild/moderate/severe), threshold (what minimum input), insensitivity (what is ignored), noise_rejection (what is filtered), resolution (what smallest change), recommendation (full_sensitivity/mild_deadband/significant_deadband/major_insensitivity_zone/narrow_deadband_range)."""

EPISTEMIC_DEADBAND_PROMPT = """Detect epistemic deadband:

Threshold: {threshold}
Insensitivity: {insensitivity}
Noise rejection: {noise_rejection}
Resolution: {resolution}
Domain: {domain}
Context: {context}

Is there a range of intellectual input where no output change occurs, creating insensitivity zones in reasoning? Return ONLY valid JSON."""


class EpistemicDeadbandService:
    """Detects epistemic deadband — insensitivity zones in reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        threshold: str,
        *,
        insensitivity: str = "",
        noise_rejection: str = "",
        resolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic deadband."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEADBAND_PROMPT.format(
                threshold=threshold,
                insensitivity=insensitivity or "Not specified",
                noise_rejection=noise_rejection or "Not specified",
                resolution=resolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEADBAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "threshold": threshold[:200],
            "deadband_present": data.get("deadband_present", False),
            "severity": data.get("severity", ""),
            "insensitivity": data.get("insensitivity", ""),
            "noise_rejection": data.get("noise_rejection", ""),
            "resolution": data.get("resolution", ""),
            "recommendation": data.get("recommendation", ""),
        }
