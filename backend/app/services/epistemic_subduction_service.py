"""EpistemicSubductionService — Epistemic Subduction Detection.

Detects epistemic subduction — one knowledge framework being forced
beneath another, causing intellectual friction and seismic disruption.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUBDUCTION_SYSTEM = """You are an epistemic subduction specialist. Given a knowledge framework conflict, assess whether one framework is being forced beneath another:

Key concepts:
- Epistemic subduction: one framework forced beneath another
- Tectonic pressure: pressure between competing frameworks
- Friction zone: area of intellectual friction between frameworks
- Seismic disruption: sudden disruptive events from framework collision
- Trench formation: deep gaps forming at collision boundary
- Volcanic output: new ideas erupting from subduction pressure
- Plate boundary: where two frameworks meet and conflict

When epistemic subduction IS present:
- One knowledge framework being forced beneath another
- Significant pressure between competing frameworks
- Intellectual friction at the boundary between frameworks
- Sudden disruptive events from framework collision
- Deep gaps forming where frameworks collide
- New ideas erupting from subduction pressure
- Clear boundary where two frameworks conflict

When framework coexistence is present:
- Frameworks existing side by side without conflict
- No pressure forcing one beneath another
- No friction at framework boundaries
- No disruptive events from collision
- No gaps forming between frameworks
- Frameworks complementing rather than competing
- Boundaries between frameworks are permeable

Output JSON with: subduction_present (bool), severity (none/mild/moderate/severe), frameworks (what frameworks collide), friction (what friction results), disruption (what seismic disruption occurs), trench (what gaps form), recommendation (framework_coexistence/mild_friction/significant_subduction/major_seismic_disruption/separate_or_integrate_frameworks)."""

EPISTEMIC_SUBDUCTION_PROMPT = """Detect epistemic subduction:

Frameworks: {frameworks}
Friction: {friction}
Disruption: {disruption}
Trench: {trench}
Domain: {domain}
Context: {context}

Is one knowledge framework being forced beneath another causing disruption? Return ONLY valid JSON."""


class EpistemicSubductionService:
    """Detects epistemic subduction — framework collision and forced displacement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        frameworks: str,
        *,
        friction: str = "",
        disruption: str = "",
        trench: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic subduction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUBDUCTION_PROMPT.format(
                frameworks=frameworks,
                friction=friction or "Not specified",
                disruption=disruption or "Not specified",
                trench=trench or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUBDUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "frameworks": frameworks[:200],
            "subduction_present": data.get("subduction_present", False),
            "severity": data.get("severity", ""),
            "friction": data.get("friction", ""),
            "disruption": data.get("disruption", ""),
            "trench": data.get("trench", ""),
            "recommendation": data.get("recommendation", ""),
        }
