"""EpistemicAvalancheService — Epistemic Avalanche Detection.

Detects epistemic avalanches — small disturbances triggering
massive cascading collapses of belief systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AVALANCHE_SYSTEM = """You are an epistemic avalanche specialist. Given a belief system, assess whether small disturbances could trigger massive cascading collapse:

Key concepts:
- Epistemic avalanche: small disturbance triggering massive collapse
- Cascade failure: failure cascading through belief system
- Trigger sensitivity: sensitivity to small triggers
- Accumulated instability: instability accumulated over time
- Chain reaction: one failure triggering chain of failures
- Disproportionate response: small cause producing large effect
- System fragility: fragility enabling avalanche

When epistemic avalanche IS present:
- Small disturbances triggering massive collapse
- Failure cascading through belief system
- High sensitivity to small triggers
- Instability accumulated making avalanche likely
- One failure triggering chain of failures
- Small cause producing disproportionately large effect
- System fragility enabling cascading collapse

When stable system is present:
- Small disturbances absorbed without cascade
- Failures contained and isolated
- Low sensitivity to triggers
- No accumulated instability
- Failures not triggering chains
- Effects proportionate to causes
- System robust against cascading failure

Output JSON with: avalanche_present (bool), severity (none/mild/moderate/severe), system (what system is vulnerable), trigger (what could trigger avalanche), cascade (how cascade would proceed), fragility (what fragility exists), recommendation (stable_system/mild_sensitivity/significant_avalanche_risk/major_cascade_vulnerability/stabilize_before_trigger)."""

EPISTEMIC_AVALANCHE_PROMPT = """Detect epistemic avalanche:

System: {system}
Trigger: {trigger}
Cascade: {cascade}
Fragility: {fragility}
Domain: {domain}
Context: {context}

Could small disturbances trigger massive cascading collapse? Return ONLY valid JSON."""


class EpistemicAvalancheService:
    """Detects epistemic avalanches — small disturbances triggering massive collapse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        trigger: str = "",
        cascade: str = "",
        fragility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic avalanche."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AVALANCHE_PROMPT.format(
                system=system,
                trigger=trigger or "Not specified",
                cascade=cascade or "Not specified",
                fragility=fragility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AVALANCHE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "avalanche_present": data.get("avalanche_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "cascade": data.get("cascade", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
