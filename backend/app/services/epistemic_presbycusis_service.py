"""EpistemicPresbycusisService — Epistemic Presbycusis Detection.

Detects epistemic presbycusis — age-related loss of ability to hear
high-frequency intellectual signals while low-frequency remains intact.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRESBYCUSIS_SYSTEM = """You are an epistemic presbycusis specialist. Given age-related intellectual hearing loss, assess presbycusis:

Key concepts:
- Epistemic presbycusis: age-related loss of high-frequency signals
- High-frequency loss: subtle, nuanced signals missed first
- Speech discrimination: understanding complex ideas degrades
- Recruitment: remaining frequencies over-amplified
- Hearing aid: amplification of lost frequencies
- Noise-in-noise: difficulty separating signal from background
- Gradual onset: slow progressive loss over time

When epistemic presbycusis IS present:
- High-frequency subtle signals being missed
- Complex idea comprehension degrading
- Remaining frequencies over-amplified
- No amplification assistance in place
- Difficulty separating signal from noise
- Gradual progressive loss occurring
- Low-frequency basics still intact

When no presbycusis:
- Full frequency range intact
- Complex ideas comprehended
- Normal amplification
- No assistance needed
- Clear signal separation
- No progressive loss
- All frequencies working

Output JSON with: presbycusis_detected (bool), severity (none/mild/moderate/severe), frequency_loss_pattern (what signals missed), discrimination_score (what comprehension level), compensation_status (what amplification), progression_rate (what speed of loss), recommendation (no_presbycusis/mild_monitoring/significant_amplification/major_comprehensive_rehabilitation/emergency_sudden_loss)."""

EPISTEMIC_PRESBYCUSIS_PROMPT = """Detect epistemic presbycusis:

Frequency loss pattern: {frequency_loss_pattern}
Discrimination score: {discrimination_score}
Compensation status: {compensation_status}
Progression rate: {progression_rate}
Domain: {domain}
Context: {context}

Is there age-related loss of ability to hear high-frequency intellectual signals? Return ONLY valid JSON."""


class EpistemicPresbycusisService:
    """Detects epistemic presbycusis — age-related high-frequency signal loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        frequency_loss_pattern: str,
        *,
        discrimination_score: str = "",
        compensation_status: str = "",
        progression_rate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic presbycusis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRESBYCUSIS_PROMPT.format(
                frequency_loss_pattern=frequency_loss_pattern,
                discrimination_score=discrimination_score or "Not specified",
                compensation_status=compensation_status or "Not specified",
                progression_rate=progression_rate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRESBYCUSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "frequency_loss_pattern": frequency_loss_pattern[:200],
            "presbycusis_detected": data.get("presbycusis_detected", False),
            "severity": data.get("severity", ""),
            "discrimination_score": data.get("discrimination_score", ""),
            "compensation_status": data.get("compensation_status", ""),
            "progression_rate": data.get("progression_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
