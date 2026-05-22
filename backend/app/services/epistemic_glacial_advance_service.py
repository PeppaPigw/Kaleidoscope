"""EpistemicGlacialAdvanceService — Epistemic Glacial Advance Detection.

Detects epistemic glacial advance — slow-moving intellectual forces
that reshape entire landscapes through sheer persistent mass.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GLACIAL_ADVANCE_SYSTEM = """You are an epistemic glacial advance specialist. Given an intellectual force pattern, assess whether slow persistent mass is reshaping the landscape:

Key concepts:
- Epistemic glacial advance: slow persistent force reshaping landscape
- Glacial pace: extremely slow but unstoppable movement
- Erosion: landscape carved by persistent pressure
- Moraine: debris deposited by advancing intellectual force
- U-shaped valley: landscape permanently reshaped by passage
- Ice age: period dominated by glacial intellectual forces
- Calving: pieces breaking off the advancing mass

When epistemic glacial advance IS present:
- Slow-moving intellectual forces reshaping entire landscapes
- Extremely slow but unstoppable intellectual movement
- Landscape being carved by persistent intellectual pressure
- Debris deposited by advancing intellectual force
- Landscape permanently reshaped by passage of force
- Period dominated by slow massive intellectual forces
- Pieces breaking off the advancing mass

When dynamic landscape is present:
- Landscape shaped by quick responsive forces
- Rapid intellectual movement and change
- No persistent pressure carving landscape
- No debris accumulation from slow forces
- Landscape maintaining its original form
- Period of dynamic intellectual activity
- Forces remaining cohesive and directed

Output JSON with: glacial_advance_present (bool), severity (none/mild/moderate/severe), force (what slow force advances), landscape (what landscape is reshaped), erosion (what is carved away), moraine (what debris is deposited), recommendation (dynamic_landscape/mild_advance/significant_glacial_force/major_landscape_reshaping/redirect_or_wait_for_retreat)."""

EPISTEMIC_GLACIAL_ADVANCE_PROMPT = """Detect epistemic glacial advance:

Force: {force}
Landscape: {landscape}
Erosion: {erosion}
Moraine: {moraine}
Domain: {domain}
Context: {context}

Are slow-moving intellectual forces reshaping entire landscapes through persistent mass? Return ONLY valid JSON."""


class EpistemicGlacialAdvanceService:
    """Detects epistemic glacial advance — slow persistent forces reshaping landscapes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        force: str,
        *,
        landscape: str = "",
        erosion: str = "",
        moraine: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic glacial advance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GLACIAL_ADVANCE_PROMPT.format(
                force=force,
                landscape=landscape or "Not specified",
                erosion=erosion or "Not specified",
                moraine=moraine or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GLACIAL_ADVANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "force": force[:200],
            "glacial_advance_present": data.get("glacial_advance_present", False),
            "severity": data.get("severity", ""),
            "landscape": data.get("landscape", ""),
            "erosion": data.get("erosion", ""),
            "moraine": data.get("moraine", ""),
            "recommendation": data.get("recommendation", ""),
        }
