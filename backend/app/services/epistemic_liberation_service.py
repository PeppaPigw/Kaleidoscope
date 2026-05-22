"""EpistemicLiberationService — Epistemic Liberation Detection.

Detects epistemic liberation — the process of freeing oneself from
illegitimate intellectual constraints and reclaiming epistemic autonomy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LIBERATION_SYSTEM = """You are an epistemic liberation specialist. Given intellectual freedom process, assess liberation:

Key concepts:
- Epistemic liberation: freeing from illegitimate constraints
- Consciousness raising: becoming aware of oppression
- Decolonization: removing imposed knowledge frameworks
- Autonomy reclamation: taking back intellectual self-governance
- Critical awakening: seeing through dominant narratives
- Voice recovery: speaking after silencing
- Knowledge sovereignty: owning one's epistemic life

When epistemic liberation IS present:
- Freeing from constraints
- Becoming aware of oppression
- Removing imposed frameworks
- Taking back self-governance
- Seeing through narratives
- Speaking after silence
- Owning epistemic life

When no liberation needed:
- Already free
- No oppression present
- Chosen frameworks
- Self-governing
- Clear-sighted
- Speaking freely
- Sovereign already

Output JSON with: liberation_detected (bool), severity (none/mild/moderate/severe), consciousness_level (what awareness), decolonization_progress (what removing), autonomy_reclamation (what taking back), voice_recovery (what speaking), recommendation (no_liberation_needed/mild_consciousness_raising/significant_liberation_process/major_intensive_decolonization/emergency_urgent_freedom)."""

EPISTEMIC_LIBERATION_PROMPT = """Detect epistemic liberation:

Consciousness level: {consciousness_level}
Decolonization progress: {decolonization_progress}
Autonomy reclamation: {autonomy_reclamation}
Voice recovery: {voice_recovery}
Domain: {domain}
Context: {context}

Is there process of freeing from illegitimate intellectual constraints? Return ONLY valid JSON."""


class EpistemicLiberationService:
    """Detects epistemic liberation — freeing from intellectual constraints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        consciousness_level: str,
        *,
        decolonization_progress: str = "",
        autonomy_reclamation: str = "",
        voice_recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic liberation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LIBERATION_PROMPT.format(
                consciousness_level=consciousness_level,
                decolonization_progress=decolonization_progress or "Not specified",
                autonomy_reclamation=autonomy_reclamation or "Not specified",
                voice_recovery=voice_recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LIBERATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "consciousness_level": consciousness_level[:200],
            "liberation_detected": data.get("liberation_detected", False),
            "severity": data.get("severity", ""),
            "decolonization_progress": data.get("decolonization_progress", ""),
            "autonomy_reclamation": data.get("autonomy_reclamation", ""),
            "voice_recovery": data.get("voice_recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }
