"""EpistemicAmblyopiaService — Epistemic Amblyopia Detection.

Detects epistemic amblyopia — lazy eye where one intellectual perspective
dominates while the other atrophies from disuse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AMBLYOPIA_SYSTEM = """You are an epistemic amblyopia specialist. Given intellectual perspective dominance with atrophy, assess amblyopia:

Key concepts:
- Epistemic amblyopia: one perspective dominates, other atrophies
- Suppression: brain ignoring input from weaker eye
- Occlusion therapy: forcing use of weaker perspective
- Critical period: window for correction
- Depth perception loss: inability to see intellectual depth
- Penalization: blurring dominant perspective to strengthen weak
- Neural pathway atrophy: disuse weakening connections

When epistemic amblyopia IS present:
- One perspective dominates completely
- Other perspective suppressed and atrophying
- Depth of understanding lost
- Critical correction window narrowing
- Neural pathways weakening from disuse
- No forced engagement with weaker view
- Monocular intellectual vision

When no amblyopia:
- Both perspectives actively engaged
- No suppression occurring
- Full depth perception present
- No atrophy from disuse
- Neural pathways healthy
- Balanced perspective use
- Binocular intellectual vision

Output JSON with: amblyopia_detected (bool), severity (none/mild/moderate/severe), dominant_perspective (what dominates), suppressed_perspective (what atrophies), depth_loss (what understanding lost), correction_window (what time remains), recommendation (no_amblyopia/mild_monitoring/significant_occlusion_therapy/major_intensive_rehabilitation/emergency_critical_period_closing)."""

EPISTEMIC_AMBLYOPIA_PROMPT = """Detect epistemic amblyopia:

Dominant perspective: {dominant_perspective}
Suppressed perspective: {suppressed_perspective}
Depth loss: {depth_loss}
Correction window: {correction_window}
Domain: {domain}
Context: {context}

Is one intellectual perspective dominating while the other atrophies from disuse? Return ONLY valid JSON."""


class EpistemicAmblyopiaService:
    """Detects epistemic amblyopia — one perspective dominates, other atrophies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dominant_perspective: str,
        *,
        suppressed_perspective: str = "",
        depth_loss: str = "",
        correction_window: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic amblyopia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AMBLYOPIA_PROMPT.format(
                dominant_perspective=dominant_perspective,
                suppressed_perspective=suppressed_perspective or "Not specified",
                depth_loss=depth_loss or "Not specified",
                correction_window=correction_window or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AMBLYOPIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dominant_perspective": dominant_perspective[:200],
            "amblyopia_detected": data.get("amblyopia_detected", False),
            "severity": data.get("severity", ""),
            "suppressed_perspective": data.get("suppressed_perspective", ""),
            "depth_loss": data.get("depth_loss", ""),
            "correction_window": data.get("correction_window", ""),
            "recommendation": data.get("recommendation", ""),
        }
