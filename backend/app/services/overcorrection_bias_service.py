"""OvercorrectionBiasService — Overcorrection Bias Detection.

Detects overcorrection bias — overcorrecting in response to discovered
errors, swinging too far in the opposite direction rather than
making proportionate adjustments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERCORRECTION_BIAS_SYSTEM = """You are an overcorrection bias specialist. Given a correction being made, assess whether the response overshoots proportionate adjustment:

Key concepts:
- Overcorrection bias: swinging too far in opposite direction
- Disproportionate response: correction larger than error warrants
- Pendulum effect: swinging from one extreme to another
- Overreaction to error: error discovery causing excessive change
- Proportionality failure: correction not proportionate to problem
- Opposite extreme: moving from one error to its mirror
- Knee-jerk correction: reflexive overcorrection

When overcorrection IS present:
- Correction larger than error warrants
- Swinging from one extreme to opposite
- Disproportionate response to discovered error
- Moving from one error to its mirror image
- Reflexive overcorrection without calibration
- Proportionality lost in correction
- New position as wrong as old but in opposite direction

When appropriate correction is present:
- Correction proportionate to error
- Adjustment calibrated to evidence
- New position between extremes
- Response measured and proportionate
- Correction informed by understanding not reaction
- Proportionality maintained in revision
- New position better supported than old

Output JSON with: overcorrection_present (bool), severity (none/mild/moderate/severe), error (what error was discovered), correction (what correction is made), proportionality (how proportionate the correction is), new_position (where the new position lands), recommendation (proportionate_correction/mild_overshoot/significant_overcorrection/major_pendulum_swing/calibrate_correction_to_evidence)."""

OVERCORRECTION_BIAS_PROMPT = """Detect overcorrection bias:

Error discovered: {error}
Correction made: {correction}
Proportionality: {proportionality}
New position: {new_position}
Domain: {domain}
Context: {context}

Is the correction overshooting proportionate adjustment? Return ONLY valid JSON."""


class OvercorrectionBiasService:
    """Detects overcorrection bias — swinging too far in opposite direction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        error: str,
        *,
        correction: str = "",
        proportionality: str = "",
        new_position: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect overcorrection bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERCORRECTION_BIAS_PROMPT.format(
                error=error,
                correction=correction or "Not specified",
                proportionality=proportionality or "Not specified",
                new_position=new_position or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OVERCORRECTION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "error": error[:200],
            "overcorrection_present": data.get("overcorrection_present", False),
            "severity": data.get("severity", ""),
            "correction": data.get("correction", ""),
            "proportionality": data.get("proportionality", ""),
            "new_position": data.get("new_position", ""),
            "recommendation": data.get("recommendation", ""),
        }
