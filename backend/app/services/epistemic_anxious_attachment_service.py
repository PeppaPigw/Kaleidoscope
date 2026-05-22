"""EpistemicAnxiousAttachmentService — Epistemic Anxious Attachment Detection.

Detects epistemic anxious attachment — anxious clinging to intellectual
authorities or ideas driven by fear of intellectual abandonment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANXIOUS_ATTACHMENT_SYSTEM = """You are an epistemic anxious attachment specialist. Given anxious clinging to intellectual authorities, assess attachment:

Key concepts:
- Epistemic anxious attachment: clinging driven by abandonment fear
- Proximity seeking: staying close to intellectual authority
- Separation anxiety: distress when authority unavailable
- Reassurance addiction: constant need for intellectual validation
- Hyperactivation: amplifying intellectual distress to get response
- Protest behavior: acting out when feeling intellectually ignored
- Preoccupation: obsessively focused on intellectual relationship

When epistemic anxious attachment IS present:
- Clinging driven by fear
- Staying close to authority
- Distress when unavailable
- Constant validation need
- Amplifying distress
- Acting out when ignored
- Obsessively focused

When no anxious attachment:
- Secure independence
- Comfortable distance
- Calm when apart
- Self-validated
- Proportionate distress
- Direct communication
- Balanced focus

Output JSON with: anxious_attachment_detected (bool), severity (none/mild/moderate/severe), proximity_seeking (what clinging to), separation_anxiety (what distress), reassurance_addiction (what needing validated), hyperactivation (what amplifying), recommendation (no_anxious_attachment/mild_security_building/significant_attachment_therapy/major_intensive_restructuring/emergency_severe_anxiety)."""

EPISTEMIC_ANXIOUS_ATTACHMENT_PROMPT = """Detect epistemic anxious attachment:

Proximity seeking: {proximity_seeking}
Separation anxiety: {separation_anxiety}
Reassurance addiction: {reassurance_addiction}
Hyperactivation: {hyperactivation}
Domain: {domain}
Context: {context}

Is there anxious clinging to intellectual authorities driven by abandonment fear? Return ONLY valid JSON."""


class EpistemicAnxiousAttachmentService:
    """Detects epistemic anxious attachment — clinging driven by abandonment fear."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        proximity_seeking: str,
        *,
        separation_anxiety: str = "",
        reassurance_addiction: str = "",
        hyperactivation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anxious attachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANXIOUS_ATTACHMENT_PROMPT.format(
                proximity_seeking=proximity_seeking,
                separation_anxiety=separation_anxiety or "Not specified",
                reassurance_addiction=reassurance_addiction or "Not specified",
                hyperactivation=hyperactivation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANXIOUS_ATTACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proximity_seeking": proximity_seeking[:200],
            "anxious_attachment_detected": data.get("anxious_attachment_detected", False),
            "severity": data.get("severity", ""),
            "separation_anxiety": data.get("separation_anxiety", ""),
            "reassurance_addiction": data.get("reassurance_addiction", ""),
            "hyperactivation": data.get("hyperactivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
