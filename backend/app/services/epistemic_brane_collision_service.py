"""EpistemicBraneCollisionService — Epistemic Brane Collision Detection.

Detects epistemic brane collision — entire intellectual frameworks colliding,
potentially creating new structures from the collision energy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRANE_COLLISION_SYSTEM = """You are an epistemic brane collision specialist. Given an intellectual event, assess whether entire frameworks are colliding:

Key concepts:
- Epistemic brane collision: entire frameworks colliding
- Ekpyrotic scenario: collision creating new intellectual big bang
- Collision energy: energy released from framework impact
- Brane separation: distance between parallel frameworks
- Moduli field: field controlling brane separation
- Reheating: collision energy creating new ideas
- Cyclic model: repeated collisions and separations

When epistemic brane collision IS present:
- Entire intellectual frameworks colliding
- Collision creating new intellectual beginnings
- Energy released from framework impact
- Measurable distance between parallel frameworks
- Controlling field governing framework separation
- Collision energy creating new ideas
- Repeated cycles of collision and separation

When isolated frameworks is present:
- Frameworks not colliding
- No collision-driven beginnings
- No impact energy
- No measurable framework distance
- No separation control
- No collision-generated ideas
- No cyclic pattern

Output JSON with: brane_collision_present (bool), severity (none/mild/moderate/severe), ekpyrotic (what new beginning), collision_energy (what released energy), brane_separation (what framework distance), cyclic (what repeated pattern), recommendation (isolated_frameworks/mild_collision/significant_brane_collision/major_framework_impact/harness_collision_energy)."""

EPISTEMIC_BRANE_COLLISION_PROMPT = """Detect epistemic brane collision:

Ekpyrotic: {ekpyrotic}
Collision energy: {collision_energy}
Brane separation: {brane_separation}
Cyclic: {cyclic}
Domain: {domain}
Context: {context}

Are entire intellectual frameworks colliding, potentially creating new structures from the collision energy? Return ONLY valid JSON."""


class EpistemicBraneCollisionService:
    """Detects epistemic brane collision — entire frameworks colliding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ekpyrotic: str,
        *,
        collision_energy: str = "",
        brane_separation: str = "",
        cyclic: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic brane collision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRANE_COLLISION_PROMPT.format(
                ekpyrotic=ekpyrotic,
                collision_energy=collision_energy or "Not specified",
                brane_separation=brane_separation or "Not specified",
                cyclic=cyclic or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRANE_COLLISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ekpyrotic": ekpyrotic[:200],
            "brane_collision_present": data.get("brane_collision_present", False),
            "severity": data.get("severity", ""),
            "collision_energy": data.get("collision_energy", ""),
            "brane_separation": data.get("brane_separation", ""),
            "cyclic": data.get("cyclic", ""),
            "recommendation": data.get("recommendation", ""),
        }
