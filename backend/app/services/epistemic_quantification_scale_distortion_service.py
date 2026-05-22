"""EpistemicQuantificationScaleDistortionService — Epistemic Scale Distortion Detection.

Detects epistemic quantification scale distortion — distorting scales to
exaggerate or minimize differences in data presentation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUANTIFICATION_SCALE_DISTORTION_SYSTEM = """You are an epistemic quantification scale distortion specialist. Given scale distortion, assess visual/numerical manipulation:

Key concepts:
- Epistemic scale distortion: distorting scales to exaggerate or minimize
- Truncated axis: starting axes at non-zero to exaggerate differences
- Logarithmic/linear switching: switching scale types to distort perception
- Aspect ratio manipulation: stretching or compressing to change visual impact
- Dual axis abuse: using dual axes to create false correlations
- Scale suppression: not showing scale to prevent proper interpretation
- Nonlinear binning: using unequal bins to distort distributions

When epistemic scale distortion IS present:
- Scales distorted to mislead
- Axes truncated
- Scale types switched strategically
- Aspect ratios manipulated
- Dual axes abused
- Scales suppressed
- Bins unequal

When no scale distortion:
- Scales appropriate and honest
- Axes start at appropriate values
- Scale types appropriate for data
- Aspect ratios proportional
- Dual axes justified
- Scales clearly shown
- Bins equal or justified

Output JSON with: scale_distortion_detected (bool), severity (none/mild/moderate/severe), truncated_axis (what axes truncated), scale_switching (what scales switched), aspect_ratio_manipulation (what ratios manipulated), dual_axis_abuse (what dual axes abused), recommendation (no_scale_distortion/mild_scale_correction/significant_visualization_reform/major_intensive_scale_audit/emergency_complete_scale_distortion)."""

EPISTEMIC_QUANTIFICATION_SCALE_DISTORTION_PROMPT = """Detect epistemic quantification scale distortion:

Truncated axis: {truncated_axis}
Scale switching: {scale_switching}
Aspect ratio manipulation: {aspect_ratio_manipulation}
Dual axis abuse: {dual_axis_abuse}
Domain: {domain}
Context: {context}

Are scales being distorted to exaggerate or minimize differences? Return ONLY valid JSON."""


class EpistemicQuantificationScaleDistortionService:
    """Detects epistemic scale distortion — visual/numerical manipulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        truncated_axis: str,
        *,
        scale_switching: str = "",
        aspect_ratio_manipulation: str = "",
        dual_axis_abuse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quantification scale distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUANTIFICATION_SCALE_DISTORTION_PROMPT.format(
                truncated_axis=truncated_axis,
                scale_switching=scale_switching or "Not specified",
                aspect_ratio_manipulation=aspect_ratio_manipulation or "Not specified",
                dual_axis_abuse=dual_axis_abuse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUANTIFICATION_SCALE_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "truncated_axis": truncated_axis[:200],
            "scale_distortion_detected": data.get("scale_distortion_detected", False),
            "severity": data.get("severity", ""),
            "scale_switching": data.get("scale_switching", ""),
            "aspect_ratio_manipulation": data.get("aspect_ratio_manipulation", ""),
            "dual_axis_abuse": data.get("dual_axis_abuse", ""),
            "recommendation": data.get("recommendation", ""),
        }
