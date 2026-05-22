"""EpistemicCavitationService — Epistemic Cavitation Detection.

Detects epistemic cavitation — vacuum bubbles forming in knowledge
flow when pressure drops, causing damage when they collapse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAVITATION_SYSTEM = """You are an epistemic cavitation specialist. Given a knowledge flow pattern, assess whether vacuum bubbles are forming:

Key concepts:
- Epistemic cavitation: vacuum bubbles forming in knowledge flow
- Pressure drop: sudden drop in intellectual pressure creating voids
- Bubble formation: empty spaces forming in knowledge
- Collapse damage: damage when knowledge voids collapse
- Flow disruption: bubbles disrupting smooth knowledge flow
- Void creation: creating empty spaces where knowledge should be
- Implosion: violent collapse of knowledge voids

When epistemic cavitation IS present:
- Vacuum bubbles forming in knowledge flow
- Sudden pressure drops creating knowledge voids
- Empty spaces forming where knowledge should be
- Damage occurring when voids collapse
- Bubbles disrupting smooth knowledge flow
- Knowledge voids being created
- Violent collapse of empty spaces causing damage

When smooth flow is present:
- No vacuum bubbles in knowledge flow
- Pressure maintained throughout flow
- No empty spaces in knowledge
- No collapse damage occurring
- Smooth uninterrupted knowledge flow
- No knowledge voids
- Stable continuous flow

Output JSON with: cavitation_present (bool), severity (none/mild/moderate/severe), flow (what flow shows cavitation), pressure_drop (what causes pressure drop), voids (what voids form), collapse_damage (what damage from collapse), recommendation (smooth_flow/mild_bubbles/significant_cavitation/major_collapse_damage/maintain_pressure)."""

EPISTEMIC_CAVITATION_PROMPT = """Detect epistemic cavitation:

Flow: {flow}
Pressure drop: {pressure_drop}
Voids: {voids}
Collapse damage: {collapse_damage}
Domain: {domain}
Context: {context}

Are vacuum bubbles forming in knowledge flow, causing damage when they collapse? Return ONLY valid JSON."""


class EpistemicCavitationService:
    """Detects epistemic cavitation — vacuum bubbles in knowledge flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flow: str,
        *,
        pressure_drop: str = "",
        voids: str = "",
        collapse_damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cavitation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAVITATION_PROMPT.format(
                flow=flow,
                pressure_drop=pressure_drop or "Not specified",
                voids=voids or "Not specified",
                collapse_damage=collapse_damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAVITATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flow": flow[:200],
            "cavitation_present": data.get("cavitation_present", False),
            "severity": data.get("severity", ""),
            "pressure_drop": data.get("pressure_drop", ""),
            "voids": data.get("voids", ""),
            "collapse_damage": data.get("collapse_damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
