"""EpistemicDarkEnergyService — Epistemic Dark Energy Detection.

Detects epistemic dark energy — unknown force accelerating knowledge
fragmentation, pushing ideas apart faster than they can connect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DARK_ENERGY_SYSTEM = """You are an epistemic dark energy specialist. Given a knowledge fragmentation pattern, assess whether unknown forces accelerate fragmentation:

Key concepts:
- Epistemic dark energy: unknown force accelerating knowledge fragmentation
- Accelerating separation: ideas moving apart faster over time
- Unknown driver: force driving fragmentation not identified
- Connection failure: ideas unable to connect despite proximity
- Expansion acceleration: rate of fragmentation increasing
- Invisible force: force not directly observable
- Coherence dissolution: coherent knowledge dissolving

When dark energy IS present:
- Unknown force accelerating knowledge fragmentation
- Ideas moving apart faster over time
- Force driving fragmentation not identified
- Ideas unable to connect despite apparent proximity
- Rate of fragmentation increasing
- Force not directly observable but effects visible
- Coherent knowledge dissolving without clear cause

When stable coherence is present:
- No unknown forces fragmenting knowledge
- Ideas maintaining connections over time
- All forces on knowledge identified
- Ideas connecting naturally
- No acceleration of fragmentation
- All forces observable and understood
- Coherent knowledge maintained

Output JSON with: dark_energy_present (bool), severity (none/mild/moderate/severe), fragmentation (what fragmentation is accelerating), unknown_force (what unknown force drives it), acceleration (how fast fragmentation accelerates), coherence_loss (what coherence is dissolving), recommendation (stable_coherence/mild_fragmentation/significant_dark_energy/major_accelerating_dissolution/identify_and_counter_force)."""

EPISTEMIC_DARK_ENERGY_PROMPT = """Detect epistemic dark energy:

Fragmentation: {fragmentation}
Unknown force: {unknown_force}
Acceleration: {acceleration}
Coherence loss: {coherence_loss}
Domain: {domain}
Context: {context}

Is an unknown force accelerating knowledge fragmentation? Return ONLY valid JSON."""


class EpistemicDarkEnergyService:
    """Detects epistemic dark energy — unknown force accelerating fragmentation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fragmentation: str,
        *,
        unknown_force: str = "",
        acceleration: str = "",
        coherence_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dark energy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DARK_ENERGY_PROMPT.format(
                fragmentation=fragmentation,
                unknown_force=unknown_force or "Not specified",
                acceleration=acceleration or "Not specified",
                coherence_loss=coherence_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DARK_ENERGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fragmentation": fragmentation[:200],
            "dark_energy_present": data.get("dark_energy_present", False),
            "severity": data.get("severity", ""),
            "unknown_force": data.get("unknown_force", ""),
            "acceleration": data.get("acceleration", ""),
            "coherence_loss": data.get("coherence_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
