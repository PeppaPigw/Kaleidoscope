"""EpistemicDetachmentService — Epistemic Detachment Detection.

Detects epistemic detachment — emotional disconnection from intellectual
content, treating ideas as purely abstract without felt significance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DETACHMENT_SYSTEM = """You are an epistemic detachment specialist. Given emotional disconnection from ideas, assess detachment:

Key concepts:
- Epistemic detachment: emotional disconnection from ideas
- Affective flatness: no emotional response to intellectual content
- Mechanical engagement: going through motions without feeling
- Dissociation: splitting off from intellectual experience
- Numbness: inability to feel about ideas
- Spectator stance: watching own thinking from outside
- Vitality loss: ideas feel dead and lifeless

When epistemic detachment IS present:
- Emotional disconnection from ideas
- No emotional response
- Going through motions
- Splitting off from experience
- Unable to feel about ideas
- Watching from outside
- Ideas feel dead

When no detachment:
- Emotionally connected to ideas
- Responsive to content
- Engaged with feeling
- Present in experience
- Feeling about ideas
- Inside own thinking
- Ideas feel alive

Output JSON with: detachment_detected (bool), severity (none/mild/moderate/severe), affective_flatness (what not feeling), mechanical_pattern (what going through motions), dissociation_level (what splitting from), vitality_loss (what feels dead), recommendation (no_detachment/mild_reconnection_practice/significant_feeling_recovery/major_intensive_reattachment/emergency_complete_dissociation)."""

EPISTEMIC_DETACHMENT_PROMPT = """Detect epistemic detachment:

Affective flatness: {affective_flatness}
Mechanical pattern: {mechanical_pattern}
Dissociation level: {dissociation_level}
Vitality loss: {vitality_loss}
Domain: {domain}
Context: {context}

Is there emotional disconnection from intellectual content? Return ONLY valid JSON."""


class EpistemicDetachmentService:
    """Detects epistemic detachment — emotional disconnection from ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        affective_flatness: str,
        *,
        mechanical_pattern: str = "",
        dissociation_level: str = "",
        vitality_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic detachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DETACHMENT_PROMPT.format(
                affective_flatness=affective_flatness,
                mechanical_pattern=mechanical_pattern or "Not specified",
                dissociation_level=dissociation_level or "Not specified",
                vitality_loss=vitality_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DETACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "affective_flatness": affective_flatness[:200],
            "detachment_detected": data.get("detachment_detected", False),
            "severity": data.get("severity", ""),
            "mechanical_pattern": data.get("mechanical_pattern", ""),
            "dissociation_level": data.get("dissociation_level", ""),
            "vitality_loss": data.get("vitality_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
