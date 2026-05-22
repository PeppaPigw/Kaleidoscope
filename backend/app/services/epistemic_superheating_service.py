"""EpistemicSuperheatingService — Epistemic Superheating Detection.

Detects epistemic superheating — ideas remaining in a solid belief state
well above the temperature where they should have melted into uncertainty.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPERHEATING_SYSTEM = """You are an epistemic superheating specialist. Given an idea state pattern, assess whether ideas remain solid above their melting point:

Key concepts:
- Epistemic superheating: beliefs persisting above melting point
- Overheating: degree above normal melting temperature
- Metastable belief: belief that should have dissolved
- Surface barrier: what prevents melting from starting
- Explosive boiling: sudden violent dissolution when triggered
- Bumping: sudden eruption of accumulated dissolution
- Leidenfrost: protective layer preventing contact with heat

When epistemic superheating IS present:
- Beliefs persisting despite evidence that should dissolve them
- Degree of counter-evidence without belief change
- Beliefs that should have dissolved but haven't
- Surface barriers preventing dissolution from starting
- Sudden violent dissolution when finally triggered
- Sudden eruption of accumulated doubt
- Protective layer preventing contact with disconfirming evidence

When normal melting is present:
- Beliefs dissolving at appropriate evidence level
- No excess counter-evidence without change
- Beliefs dissolving when they should
- No barriers to appropriate dissolution
- Gradual dissolution as counter-evidence accumulates
- Smooth doubt accumulation
- Direct contact with all evidence

Output JSON with: superheating_present (bool), severity (none/mild/moderate/severe), overheating (what excess counter-evidence), surface_barrier (what prevents melting), explosive_boiling (what sudden dissolution), leidenfrost (what protective layer), recommendation (normal_melting/mild_superheating/significant_superheating/major_belief_persistence/remove_protective_barrier)."""

EPISTEMIC_SUPERHEATING_PROMPT = """Detect epistemic superheating:

Overheating: {overheating}
Surface barrier: {surface_barrier}
Explosive boiling: {explosive_boiling}
Leidenfrost: {leidenfrost}
Domain: {domain}
Context: {context}

Are ideas remaining in a solid belief state well above the temperature where they should have melted into uncertainty? Return ONLY valid JSON."""


class EpistemicSuperheatingService:
    """Detects epistemic superheating — beliefs persisting above melting point."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        overheating: str,
        *,
        surface_barrier: str = "",
        explosive_boiling: str = "",
        leidenfrost: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic superheating."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPERHEATING_PROMPT.format(
                overheating=overheating,
                surface_barrier=surface_barrier or "Not specified",
                explosive_boiling=explosive_boiling or "Not specified",
                leidenfrost=leidenfrost or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPERHEATING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overheating": overheating[:200],
            "superheating_present": data.get("superheating_present", False),
            "severity": data.get("severity", ""),
            "surface_barrier": data.get("surface_barrier", ""),
            "explosive_boiling": data.get("explosive_boiling", ""),
            "leidenfrost": data.get("leidenfrost", ""),
            "recommendation": data.get("recommendation", ""),
        }
