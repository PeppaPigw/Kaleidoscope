"""EpistemicEczemaService — Epistemic Eczema Detection.

Detects epistemic eczema — chronic itchy inflammation of intellectual surface
causing compulsive scratching that worsens the condition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECZEMA_SYSTEM = """You are an epistemic eczema specialist. Given chronic intellectual surface inflammation with scratch cycle, assess eczema:

Key concepts:
- Epistemic eczema: chronic itchy inflammation of intellectual surface
- Itch-scratch cycle: compulsive engagement worsening condition
- Flare: acute worsening of chronic condition
- Barrier dysfunction: protective surface compromised
- Trigger identification: what provokes flares
- Emollient therapy: restoring surface moisture/protection
- Steroid response: anti-inflammatory intervention

When epistemic eczema IS present:
- Chronic itchy inflammation of surface
- Compulsive scratching worsening condition
- Acute flares occurring
- Protective barrier compromised
- Triggers provoking episodes
- Surface moisture/protection lost
- Anti-inflammatory intervention needed

When no eczema:
- No chronic surface inflammation
- No compulsive engagement cycle
- No acute flares
- Protective barrier intact
- No trigger sensitivity
- Surface well-protected
- No intervention needed

Output JSON with: eczema_detected (bool), severity (none/mild/moderate/severe), inflammation_pattern (what surface affected), scratch_cycle (what compulsive engagement), barrier_status (what protection level), trigger_identified (what provokes), recommendation (no_eczema/mild_emollient/significant_topical_treatment/major_systemic_therapy/emergency_acute_flare)."""

EPISTEMIC_ECZEMA_PROMPT = """Detect epistemic eczema:

Inflammation pattern: {inflammation_pattern}
Scratch cycle: {scratch_cycle}
Barrier status: {barrier_status}
Trigger identified: {trigger_identified}
Domain: {domain}
Context: {context}

Is there chronic itchy inflammation of intellectual surface with compulsive scratching worsening it? Return ONLY valid JSON."""


class EpistemicEczemaService:
    """Detects epistemic eczema — chronic itchy inflammation with scratch cycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inflammation_pattern: str,
        *,
        scratch_cycle: str = "",
        barrier_status: str = "",
        trigger_identified: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic eczema."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECZEMA_PROMPT.format(
                inflammation_pattern=inflammation_pattern,
                scratch_cycle=scratch_cycle or "Not specified",
                barrier_status=barrier_status or "Not specified",
                trigger_identified=trigger_identified or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECZEMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inflammation_pattern": inflammation_pattern[:200],
            "eczema_detected": data.get("eczema_detected", False),
            "severity": data.get("severity", ""),
            "scratch_cycle": data.get("scratch_cycle", ""),
            "barrier_status": data.get("barrier_status", ""),
            "trigger_identified": data.get("trigger_identified", ""),
            "recommendation": data.get("recommendation", ""),
        }
