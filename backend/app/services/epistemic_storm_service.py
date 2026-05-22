"""EpistemicStormService — Epistemic Storm Detection.

Detects epistemic storms — violent intellectual turbulence
disrupting coherent thought and productive discourse.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STORM_SYSTEM = """You are an epistemic storm specialist. Given a discourse situation, assess whether violent intellectual turbulence is disrupting coherent thought:

Key concepts:
- Epistemic storm: violent intellectual turbulence
- Discourse disruption: productive discourse disrupted
- Idea turbulence: ideas in chaotic motion
- Coherence destruction: coherent thought destroyed
- Intellectual violence: violent clash of ideas
- Productive destruction: whether destruction enables renewal
- Storm aftermath: what remains after turbulence passes

When epistemic storm IS present:
- Violent intellectual turbulence disrupting thought
- Productive discourse disrupted by chaotic forces
- Ideas in chaotic, uncontrolled motion
- Coherent thought destroyed by turbulence
- Violent clash of ideas preventing progress
- Destruction without clear productive purpose
- Aftermath leaving intellectual landscape damaged

When productive debate is present:
- Vigorous but controlled intellectual exchange
- Discourse energized but not disrupted
- Ideas in dynamic but navigable motion
- Coherent thought maintained through disagreement
- Clash of ideas producing refinement
- Energy channeled productively
- Exchange leaving landscape enriched

Output JSON with: storm_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), turbulence (what turbulence manifests), disruption (what is disrupted), aftermath (what aftermath results), recommendation (productive_debate/mild_turbulence/significant_storm/major_intellectual_violence/shelter_and_wait)."""

EPISTEMIC_STORM_PROMPT = """Detect epistemic storm:

Situation: {situation}
Turbulence: {turbulence}
Disruption: {disruption}
Aftermath: {aftermath}
Domain: {domain}
Context: {context}

Is violent intellectual turbulence disrupting coherent thought? Return ONLY valid JSON."""


class EpistemicStormService:
    """Detects epistemic storms — violent intellectual turbulence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        turbulence: str = "",
        disruption: str = "",
        aftermath: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic storm."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STORM_PROMPT.format(
                situation=situation,
                turbulence=turbulence or "Not specified",
                disruption=disruption or "Not specified",
                aftermath=aftermath or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STORM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "storm_present": data.get("storm_present", False),
            "severity": data.get("severity", ""),
            "turbulence": data.get("turbulence", ""),
            "disruption": data.get("disruption", ""),
            "aftermath": data.get("aftermath", ""),
            "recommendation": data.get("recommendation", ""),
        }
