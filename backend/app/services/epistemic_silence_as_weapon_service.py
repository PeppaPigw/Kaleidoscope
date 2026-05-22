"""EpistemicSilenceAsWeaponService — Epistemic Silence As Weapon Detection.

Detects epistemic silence as weapon — using silence strategically
to control epistemic dynamics.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SILENCE_AS_WEAPON_SYSTEM = """You are an epistemic silence as weapon specialist. Given using silence to control dynamics, assess silence as weapon:

Key concepts:
- Epistemic silence as weapon: using silence to control epistemic dynamics
- Strategic withholding: withholding information to maintain power
- Silence as punishment: refusing to share knowledge as punishment
- Information embargo: deliberately cutting off information flow
- Passive aggression: using silence to express intellectual hostility
- Exclusion through silence: excluding by not sharing
- Power through absence: controlling through what's not said

When epistemic silence as weapon IS present:
- Using silence to control
- Withholding to maintain power
- Refusing to share as punishment
- Cutting off information flow
- Silence expressing hostility
- Excluding by not sharing
- Controlling through absence

When no silence as weapon:
- Silence as reflection
- Sharing freely
- Generous with knowledge
- Open information flow
- Silence as peace
- Including through sharing
- Presence through contribution

Output JSON with: silence_as_weapon_detected (bool), severity (none/mild/moderate/severe), strategic_withholding (what withholding for power), silence_as_punishment (what refusing to share as punishment), information_embargo (what cutting off flow of), exclusion_through_silence (what excluding by not sharing), recommendation (no_silence_weapon/mild_sharing_practice/significant_generosity_building/major_intensive_openness_work/emergency_complete_information_warfare)."""

EPISTEMIC_SILENCE_AS_WEAPON_PROMPT = """Detect epistemic silence as weapon:

Strategic withholding: {strategic_withholding}
Silence as punishment: {silence_as_punishment}
Information embargo: {information_embargo}
Exclusion through silence: {exclusion_through_silence}
Domain: {domain}
Context: {context}

Is there using silence strategically to control epistemic dynamics? Return ONLY valid JSON."""


class EpistemicSilenceAsWeaponService:
    """Detects epistemic silence as weapon — using silence to control dynamics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategic_withholding: str,
        *,
        silence_as_punishment: str = "",
        information_embargo: str = "",
        exclusion_through_silence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic silence as weapon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SILENCE_AS_WEAPON_PROMPT.format(
                strategic_withholding=strategic_withholding,
                silence_as_punishment=silence_as_punishment or "Not specified",
                information_embargo=information_embargo or "Not specified",
                exclusion_through_silence=exclusion_through_silence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SILENCE_AS_WEAPON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategic_withholding": strategic_withholding[:200],
            "silence_as_weapon_detected": data.get("silence_as_weapon_detected", False),
            "severity": data.get("severity", ""),
            "silence_as_punishment": data.get("silence_as_punishment", ""),
            "information_embargo": data.get("information_embargo", ""),
            "exclusion_through_silence": data.get("exclusion_through_silence", ""),
            "recommendation": data.get("recommendation", ""),
        }
