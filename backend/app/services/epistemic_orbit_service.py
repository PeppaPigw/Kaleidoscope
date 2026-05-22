"""EpistemicOrbitService — Epistemic Orbit Detection.

Detects epistemic orbits — ideas trapped orbiting a central concept
without escape, endlessly circling without progress.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ORBIT_SYSTEM = """You are an epistemic orbit specialist. Given a discourse pattern, assess whether ideas are trapped orbiting a central concept without progress:

Key concepts:
- Epistemic orbit: ideas trapped circling a central concept
- Circular discourse: discourse going in circles
- Progress failure: failure to make progress despite activity
- Conceptual trap: trapped in orbit around one concept
- Escape failure: inability to escape circular pattern
- Repetitive cycling: cycling through same ideas repeatedly
- Orbital decay: gradually losing energy without resolution

When epistemic orbit IS present:
- Ideas trapped orbiting central concept without escape
- Discourse going in circles without progress
- Activity present but progress absent
- Trapped in orbit around one concept
- Unable to escape circular pattern
- Same ideas cycled through repeatedly
- Energy spent without resolution

When productive focus is present:
- Focus on central concept with progress
- Discussion deepening not circling
- Activity producing genuine advancement
- Engagement with concept producing insight
- Ability to move beyond when ready
- Ideas building on each other
- Energy producing resolution

Output JSON with: orbit_present (bool), severity (none/mild/moderate/severe), discourse (what discourse is affected), central_concept (what concept is orbited), cycling (how cycling manifests), escape_failure (why escape fails), recommendation (productive_focus/mild_repetition/significant_epistemic_orbit/major_circular_trap/break_orbital_pattern)."""

EPISTEMIC_ORBIT_PROMPT = """Detect epistemic orbit:

Discourse: {discourse}
Central concept: {central}
Cycling pattern: {cycling}
Progress: {progress}
Domain: {domain}
Context: {context}

Are ideas trapped orbiting a central concept without progress? Return ONLY valid JSON."""


class EpistemicOrbitService:
    """Detects epistemic orbits — ideas trapped circling without progress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        central: str = "",
        cycling: str = "",
        progress: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic orbit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ORBIT_PROMPT.format(
                discourse=discourse,
                central=central or "Not specified",
                cycling=cycling or "Not specified",
                progress=progress or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ORBIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "orbit_present": data.get("orbit_present", False),
            "severity": data.get("severity", ""),
            "central_concept": data.get("central_concept", ""),
            "cycling": data.get("cycling", ""),
            "escape_failure": data.get("escape_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
