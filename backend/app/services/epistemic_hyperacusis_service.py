"""EpistemicHyperacusisService — Epistemic Hyperacusis Detection.

Detects epistemic hyperacusis — painful oversensitivity to intellectual
input at normal volumes, where ordinary ideas cause distress.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYPERACUSIS_SYSTEM = """You are an epistemic hyperacusis specialist. Given painful intellectual oversensitivity, assess hyperacusis:

Key concepts:
- Epistemic hyperacusis: painful oversensitivity to normal input
- Loudness discomfort level: threshold where input becomes painful
- Recruitment: abnormal growth of perceived loudness
- Sound therapy: gradual desensitization with controlled input
- Avoidance behavior: withdrawing from intellectual stimulation
- Central gain: brain amplifying signals excessively
- Phonophobia: fear of intellectual input due to pain

When epistemic hyperacusis IS present:
- Normal input causing pain or distress
- Very low discomfort threshold
- Abnormal amplification of input
- No desensitization occurring
- Withdrawing from stimulation
- Brain over-amplifying signals
- Fear of intellectual input

When no hyperacusis:
- Normal input tolerated well
- Appropriate discomfort threshold
- Normal signal processing
- Natural tolerance present
- Engaging with stimulation
- Appropriate signal gain
- No fear of input

Output JSON with: hyperacusis_detected (bool), severity (none/mild/moderate/severe), discomfort_threshold (what triggers pain), amplification_pattern (what over-processing), avoidance_behavior (what withdrawal), desensitization_status (what tolerance building), recommendation (no_hyperacusis/mild_sound_therapy/significant_structured_desensitization/major_comprehensive_treatment/emergency_acute_phonophobia)."""

EPISTEMIC_HYPERACUSIS_PROMPT = """Detect epistemic hyperacusis:

Discomfort threshold: {discomfort_threshold}
Amplification pattern: {amplification_pattern}
Avoidance behavior: {avoidance_behavior}
Desensitization status: {desensitization_status}
Domain: {domain}
Context: {context}

Is there painful oversensitivity to intellectual input at normal volumes? Return ONLY valid JSON."""


class EpistemicHyperacusisService:
    """Detects epistemic hyperacusis — painful oversensitivity to normal input."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discomfort_threshold: str,
        *,
        amplification_pattern: str = "",
        avoidance_behavior: str = "",
        desensitization_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hyperacusis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYPERACUSIS_PROMPT.format(
                discomfort_threshold=discomfort_threshold,
                amplification_pattern=amplification_pattern or "Not specified",
                avoidance_behavior=avoidance_behavior or "Not specified",
                desensitization_status=desensitization_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYPERACUSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discomfort_threshold": discomfort_threshold[:200],
            "hyperacusis_detected": data.get("hyperacusis_detected", False),
            "severity": data.get("severity", ""),
            "amplification_pattern": data.get("amplification_pattern", ""),
            "avoidance_behavior": data.get("avoidance_behavior", ""),
            "desensitization_status": data.get("desensitization_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
