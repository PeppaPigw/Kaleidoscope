"""EpistemicHemorrhageService — Epistemic Hemorrhage Detection.

Detects epistemic hemorrhage — uncontrolled loss of intellectual substance,
where ideas bleed out faster than they can be replenished.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HEMORRHAGE_SYSTEM = """You are an epistemic hemorrhage specialist. Given intellectual substance loss, assess whether uncontrolled bleeding is occurring:

Key concepts:
- Epistemic hemorrhage: uncontrolled loss of intellectual substance
- Arterial bleed: high-pressure rapid loss from major vessel
- Venous ooze: slower steady loss from damaged veins
- Hemorrhagic shock: systemic failure from volume loss
- Tamponade: pressure stopping the bleed
- Coagulopathy: inability to form clots to stop bleeding
- Transfusion: replacing lost intellectual volume

When epistemic hemorrhage IS present:
- Uncontrolled loss of intellectual substance
- High-pressure rapid idea loss
- Slower steady knowledge drain
- Systemic failure from intellectual volume loss
- Need for pressure to stop the bleed
- Inability to self-seal intellectual wounds
- Need for external intellectual replacement

When healthy containment is present:
- Intellectual substance retained
- No rapid idea loss
- No steady knowledge drain
- Stable intellectual volume
- Self-sealing intellectual boundaries
- Normal clotting ability
- Self-sufficient intellectual volume

Output JSON with: hemorrhage_present (bool), severity (none/mild/moderate/severe), arterial_bleed (what rapid loss), venous_ooze (what steady drain), hemorrhagic_shock (what systemic failure), coagulopathy (what clotting failure), recommendation (healthy_containment/mild_hemorrhage/significant_hemorrhage/major_intellectual_bleed/tamponade_intellectual_loss)."""

EPISTEMIC_HEMORRHAGE_PROMPT = """Detect epistemic hemorrhage:

Arterial bleed: {arterial_bleed}
Venous ooze: {venous_ooze}
Hemorrhagic shock: {hemorrhagic_shock}
Coagulopathy: {coagulopathy}
Domain: {domain}
Context: {context}

Is there uncontrolled loss of intellectual substance, with ideas bleeding out faster than replenishment? Return ONLY valid JSON."""


class EpistemicHemorrhageService:
    """Detects epistemic hemorrhage — uncontrolled intellectual substance loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arterial_bleed: str,
        *,
        venous_ooze: str = "",
        hemorrhagic_shock: str = "",
        coagulopathy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hemorrhage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HEMORRHAGE_PROMPT.format(
                arterial_bleed=arterial_bleed,
                venous_ooze=venous_ooze or "Not specified",
                hemorrhagic_shock=hemorrhagic_shock or "Not specified",
                coagulopathy=coagulopathy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HEMORRHAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arterial_bleed": arterial_bleed[:200],
            "hemorrhage_present": data.get("hemorrhage_present", False),
            "severity": data.get("severity", ""),
            "venous_ooze": data.get("venous_ooze", ""),
            "hemorrhagic_shock": data.get("hemorrhagic_shock", ""),
            "coagulopathy": data.get("coagulopathy", ""),
            "recommendation": data.get("recommendation", ""),
        }
