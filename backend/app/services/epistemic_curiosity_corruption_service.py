"""EpistemicCuriosityCorruptionService — Epistemic Curiosity Corruption Detection.

Detects epistemic curiosity corruption — curiosity corrupted by external
rewards rather than genuine desire to know.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CURIOSITY_CORRUPTION_SYSTEM = """You are an epistemic curiosity corruption specialist. Given curiosity corrupted by external rewards, assess curiosity corruption:

Key concepts:
- Epistemic curiosity corruption: curiosity driven by rewards not genuine desire
- Extrinsic motivation: learning for grades/status not understanding
- Curiosity commodification: turning wonder into productivity metric
- Instrumental learning: learning only what's useful not interesting
- Reward hijacking: external rewards replacing intrinsic motivation
- Curiosity performance: appearing curious for social benefit
- Wonder death: genuine curiosity killed by reward systems

When epistemic curiosity corruption IS present:
- Curiosity driven by rewards not desire
- Learning for status not understanding
- Wonder turned into metric
- Learning only useful things
- Rewards replacing motivation
- Appearing curious for benefit
- Genuine curiosity killed

When no curiosity corruption:
- Genuine curiosity
- Learning for understanding
- Wonder preserved
- Learning from interest
- Intrinsic motivation
- Authentic curiosity
- Wonder alive

Output JSON with: curiosity_corruption_detected (bool), severity (none/mild/moderate/severe), extrinsic_motivation (what learning for rewards), curiosity_commodification (what turning into metric), instrumental_learning (what learning only for utility), wonder_death (what genuine curiosity killed by), recommendation (no_curiosity_corruption/mild_intrinsic_reconnection/significant_wonder_recovery/major_intensive_motivation_repair/emergency_complete_curiosity_death)."""

EPISTEMIC_CURIOSITY_CORRUPTION_PROMPT = """Detect epistemic curiosity corruption:

Extrinsic motivation: {extrinsic_motivation}
Curiosity commodification: {curiosity_commodification}
Instrumental learning: {instrumental_learning}
Wonder death: {wonder_death}
Domain: {domain}
Context: {context}

Is there curiosity corrupted by external rewards rather than genuine desire to know? Return ONLY valid JSON."""


class EpistemicCuriosityCorruptionService:
    """Detects epistemic curiosity corruption — curiosity corrupted by external rewards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        extrinsic_motivation: str,
        *,
        curiosity_commodification: str = "",
        instrumental_learning: str = "",
        wonder_death: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic curiosity corruption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CURIOSITY_CORRUPTION_PROMPT.format(
                extrinsic_motivation=extrinsic_motivation,
                curiosity_commodification=curiosity_commodification or "Not specified",
                instrumental_learning=instrumental_learning or "Not specified",
                wonder_death=wonder_death or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CURIOSITY_CORRUPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "extrinsic_motivation": extrinsic_motivation[:200],
            "curiosity_corruption_detected": data.get("curiosity_corruption_detected", False),
            "severity": data.get("severity", ""),
            "curiosity_commodification": data.get("curiosity_commodification", ""),
            "instrumental_learning": data.get("instrumental_learning", ""),
            "wonder_death": data.get("wonder_death", ""),
            "recommendation": data.get("recommendation", ""),
        }
