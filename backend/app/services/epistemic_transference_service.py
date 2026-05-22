"""EpistemicTransferenceService — Epistemic Transference Detection.

Detects epistemic transference — unconsciously redirecting intellectual
feelings about past authorities onto current intellectual relationships.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRANSFERENCE_SYSTEM = """You are an epistemic transference specialist. Given redirected intellectual feelings, assess transference:

Key concepts:
- Epistemic transference: redirecting feelings about past onto present
- Past authority: previous intellectual figure being replayed
- Current target: present person receiving displaced feelings
- Repetition: same relational pattern recurring
- Distortion: seeing current person through past lens
- Intensity mismatch: feelings disproportionate to current situation
- Template: using old relationship as blueprint for new

When epistemic transference IS present:
- Redirecting past feelings
- Previous figure being replayed
- Present person receiving displacement
- Same pattern recurring
- Seeing through past lens
- Feelings disproportionate
- Old blueprint applied

When no transference:
- Present-focused feelings
- No past replay
- Seeing person accurately
- Fresh patterns
- Clear current perception
- Proportionate feelings
- New relationship template

Output JSON with: transference_detected (bool), severity (none/mild/moderate/severe), past_authority (what previous figure), repetition_pattern (what recurring), distortion_type (what past lens), intensity_mismatch (what disproportionate), recommendation (no_transference/mild_awareness_building/significant_transference_analysis/major_intensive_therapy/emergency_severe_distortion)."""

EPISTEMIC_TRANSFERENCE_PROMPT = """Detect epistemic transference:

Past authority: {past_authority}
Repetition pattern: {repetition_pattern}
Distortion type: {distortion_type}
Intensity mismatch: {intensity_mismatch}
Domain: {domain}
Context: {context}

Is there unconscious redirection of feelings about past authorities onto current relationships? Return ONLY valid JSON."""


class EpistemicTransferenceService:
    """Detects epistemic transference — redirecting past feelings onto present."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        past_authority: str,
        *,
        repetition_pattern: str = "",
        distortion_type: str = "",
        intensity_mismatch: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic transference."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRANSFERENCE_PROMPT.format(
                past_authority=past_authority,
                repetition_pattern=repetition_pattern or "Not specified",
                distortion_type=distortion_type or "Not specified",
                intensity_mismatch=intensity_mismatch or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRANSFERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "past_authority": past_authority[:200],
            "transference_detected": data.get("transference_detected", False),
            "severity": data.get("severity", ""),
            "repetition_pattern": data.get("repetition_pattern", ""),
            "distortion_type": data.get("distortion_type", ""),
            "intensity_mismatch": data.get("intensity_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }
