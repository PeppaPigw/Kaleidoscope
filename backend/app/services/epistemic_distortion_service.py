"""EpistemicDistortionService — Epistemic Distortion Detection.

Detects epistemic distortion — knowledge signal clipped or saturated,
losing nuance at extremes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISTORTION_SYSTEM = """You are an epistemic distortion specialist. Given a knowledge signal, assess whether it has been clipped or saturated losing nuance:

Key concepts:
- Epistemic distortion: knowledge signal clipped or saturated
- Clipping: extreme values cut off, losing nuance at extremes
- Saturation: signal maxed out, unable to represent higher values
- Dynamic range loss: losing ability to distinguish between levels
- Nuance destruction: subtle differences destroyed
- Binary collapse: continuous spectrum collapsed to binary
- Overdriving: pushing knowledge beyond its representational capacity

When epistemic distortion IS present:
- Knowledge signal clipped at extremes
- Nuance lost at high or low values
- Signal saturated and unable to represent full range
- Dynamic range compressed or lost
- Subtle differences destroyed
- Continuous spectrum collapsed to binary or few categories
- Knowledge pushed beyond representational capacity

When undistorted signal is present:
- Full range of knowledge preserved
- Nuance maintained at all levels
- Signal within representational capacity
- Full dynamic range available
- Subtle differences preserved
- Continuous spectrum maintained
- Knowledge within representational capacity

Output JSON with: distortion_present (bool), severity (none/mild/moderate/severe), signal (what knowledge signal is distorted), clipping (what is clipped), saturation (what is saturated), nuance_lost (what nuance is destroyed), recommendation (undistorted_signal/mild_clipping/significant_distortion/major_saturation/restore_dynamic_range)."""

EPISTEMIC_DISTORTION_PROMPT = """Detect epistemic distortion:

Signal: {signal}
Clipping: {clipping}
Saturation: {saturation}
Nuance lost: {nuance_lost}
Domain: {domain}
Context: {context}

Is the knowledge signal clipped or saturated, losing nuance at extremes? Return ONLY valid JSON."""


class EpistemicDistortionService:
    """Detects epistemic distortion — knowledge signal clipped or saturated."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        signal: str,
        *,
        clipping: str = "",
        saturation: str = "",
        nuance_lost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISTORTION_PROMPT.format(
                signal=signal,
                clipping=clipping or "Not specified",
                saturation=saturation or "Not specified",
                nuance_lost=nuance_lost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "signal": signal[:200],
            "distortion_present": data.get("distortion_present", False),
            "severity": data.get("severity", ""),
            "clipping": data.get("clipping", ""),
            "saturation": data.get("saturation", ""),
            "nuance_lost": data.get("nuance_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
