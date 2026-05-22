"""EpistemicRiptideService — Epistemic Riptide Detection.

Detects epistemic riptide — hidden intellectual currents that pull
thinkers away from shore into dangerous deep waters.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RIPTIDE_SYSTEM = """You are an epistemic riptide specialist. Given a thinking pattern, assess whether hidden currents pull thinkers into dangerous territory:

Key concepts:
- Epistemic riptide: hidden currents pulling thinkers into danger
- Hidden current: invisible intellectual force pulling in one direction
- Shore: safe established knowledge
- Deep water: dangerous uncharted intellectual territory
- Swimmer exhaustion: intellectual exhaustion from fighting the current
- Channel: narrow path through which the riptide flows
- Escape: swimming parallel to shore rather than against current

When epistemic riptide IS present:
- Hidden intellectual currents pulling thinkers away from safety
- Invisible forces pulling thinking in one direction
- Thinkers being pulled away from established knowledge
- Being drawn into dangerous uncharted territory
- Intellectual exhaustion from fighting hidden currents
- Narrow channels concentrating the pulling force
- Difficulty escaping the pull of the current

When safe intellectual waters are present:
- No hidden currents pulling thinkers off course
- Intellectual forces visible and manageable
- Thinkers remaining in safe established territory
- No pull toward dangerous uncharted areas
- No intellectual exhaustion from hidden forces
- No concentrated channels of force
- Easy to maintain chosen intellectual direction

Output JSON with: riptide_present (bool), severity (none/mild/moderate/severe), current (what hidden current pulls), shore (what safe knowledge is left behind), deep_water (what dangerous territory), exhaustion (what exhaustion results), recommendation (safe_waters/mild_current/significant_riptide/major_danger/swim_parallel_to_shore)."""

EPISTEMIC_RIPTIDE_PROMPT = """Detect epistemic riptide:

Current: {current}
Shore: {shore}
Deep water: {deep_water}
Exhaustion: {exhaustion}
Domain: {domain}
Context: {context}

Are hidden intellectual currents pulling thinkers away from safety into dangerous territory? Return ONLY valid JSON."""


class EpistemicRiptideService:
    """Detects epistemic riptide — hidden currents pulling toward danger."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        current: str,
        *,
        shore: str = "",
        deep_water: str = "",
        exhaustion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic riptide."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RIPTIDE_PROMPT.format(
                current=current,
                shore=shore or "Not specified",
                deep_water=deep_water or "Not specified",
                exhaustion=exhaustion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RIPTIDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "current": current[:200],
            "riptide_present": data.get("riptide_present", False),
            "severity": data.get("severity", ""),
            "shore": data.get("shore", ""),
            "deep_water": data.get("deep_water", ""),
            "exhaustion": data.get("exhaustion", ""),
            "recommendation": data.get("recommendation", ""),
        }
