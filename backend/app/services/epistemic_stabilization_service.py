"""EpistemicStabilizationService — Epistemic Stabilization Detection.

Detects need for epistemic stabilization — preventing further deterioration
of intellectual injury while definitive treatment is arranged.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STABILIZATION_SYSTEM = """You are an epistemic stabilization specialist. Given intellectual injury, assess whether stabilization is needed to prevent deterioration:

Key concepts:
- Epistemic stabilization: preventing further intellectual deterioration
- Immobilization: preventing movement that worsens injury
- Hemorrhage control: stopping intellectual substance loss
- Splinting: external support for damaged structures
- Monitoring: watching for signs of deterioration
- Damage control: minimum intervention to prevent death
- Golden hour: critical time window for intervention

When epistemic stabilization IS needed:
- Active deterioration of intellectual injury
- Movement worsening the damage
- Ongoing intellectual substance loss
- Damaged structures needing support
- Signs of deterioration present
- Minimum intervention needed to prevent death
- Critical time window closing

When no stabilization needed:
- Stable intellectual state
- No active deterioration
- No ongoing loss
- Structures self-supporting
- No deterioration signs
- No urgent intervention needed
- No time pressure

Output JSON with: stabilization_needed (bool), severity (none/mild/moderate/severe), immobilization (what movement prevention), hemorrhage_control (what loss stopping), damage_control (what minimum intervention), golden_hour (what time pressure), recommendation (no_stabilization_needed/mild_stabilization/significant_stabilization/major_damage_control/emergency_intellectual_stabilization)."""

EPISTEMIC_STABILIZATION_PROMPT = """Detect epistemic stabilization need:

Immobilization: {immobilization}
Hemorrhage control: {hemorrhage_control}
Damage control: {damage_control}
Golden hour: {golden_hour}
Domain: {domain}
Context: {context}

Is stabilization needed to prevent further intellectual deterioration? Return ONLY valid JSON."""


class EpistemicStabilizationService:
    """Detects epistemic stabilization need — preventing intellectual deterioration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        immobilization: str,
        *,
        hemorrhage_control: str = "",
        damage_control: str = "",
        golden_hour: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stabilization need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STABILIZATION_PROMPT.format(
                immobilization=immobilization,
                hemorrhage_control=hemorrhage_control or "Not specified",
                damage_control=damage_control or "Not specified",
                golden_hour=golden_hour or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STABILIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "immobilization": immobilization[:200],
            "stabilization_needed": data.get("stabilization_needed", False),
            "severity": data.get("severity", ""),
            "hemorrhage_control": data.get("hemorrhage_control", ""),
            "damage_control": data.get("damage_control", ""),
            "golden_hour": data.get("golden_hour", ""),
            "recommendation": data.get("recommendation", ""),
        }
