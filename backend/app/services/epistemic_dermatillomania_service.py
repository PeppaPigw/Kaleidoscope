"""EpistemicDermatillomaniaService — Epistemic Dermatillomania Detection.

Detects epistemic dermatillomania — compulsive picking at intellectual
flaws, obsessively finding and excavating imperfections in own work.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DERMATILLOMANIA_SYSTEM = """You are an epistemic dermatillomania specialist. Given compulsive flaw-picking, assess dermatillomania:

Key concepts:
- Epistemic dermatillomania: compulsive picking at intellectual flaws
- Scanning: constantly searching for imperfections
- Excavating: digging deeper into found flaws
- Worsening: picking makes flaws worse not better
- Inability to stop: continuing despite damage
- Perfectionism: driven by need for flawless work
- Scarring: permanent damage from excessive picking

When epistemic dermatillomania IS present:
- Compulsive flaw-picking
- Constantly searching for imperfections
- Digging deeper into flaws
- Making flaws worse
- Continuing despite damage
- Driven by perfectionism
- Permanent damage from picking

When no dermatillomania:
- Accepting imperfections
- Not searching for flaws
- Proportionate attention to issues
- Fixing improves work
- Stopping when adequate
- Comfortable with good enough
- No damage from process

Output JSON with: dermatillomania_detected (bool), severity (none/mild/moderate/severe), picking_pattern (what flaw excavation), scanning_behavior (what searching), worsening_effect (what damage from picking), stop_difficulty (what inability to cease), recommendation (no_dermatillomania/mild_habit_reversal/significant_cbt/major_intensive_therapy/emergency_severe_damage)."""

EPISTEMIC_DERMATILLOMANIA_PROMPT = """Detect epistemic dermatillomania:

Picking pattern: {picking_pattern}
Scanning behavior: {scanning_behavior}
Worsening effect: {worsening_effect}
Stop difficulty: {stop_difficulty}
Domain: {domain}
Context: {context}

Is there compulsive picking at intellectual flaws, obsessively excavating imperfections? Return ONLY valid JSON."""


class EpistemicDermatillomaniaService:
    """Detects epistemic dermatillomania — compulsive flaw-picking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        picking_pattern: str,
        *,
        scanning_behavior: str = "",
        worsening_effect: str = "",
        stop_difficulty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dermatillomania."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DERMATILLOMANIA_PROMPT.format(
                picking_pattern=picking_pattern,
                scanning_behavior=scanning_behavior or "Not specified",
                worsening_effect=worsening_effect or "Not specified",
                stop_difficulty=stop_difficulty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DERMATILLOMANIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "picking_pattern": picking_pattern[:200],
            "dermatillomania_detected": data.get("dermatillomania_detected", False),
            "severity": data.get("severity", ""),
            "scanning_behavior": data.get("scanning_behavior", ""),
            "worsening_effect": data.get("worsening_effect", ""),
            "stop_difficulty": data.get("stop_difficulty", ""),
            "recommendation": data.get("recommendation", ""),
        }
