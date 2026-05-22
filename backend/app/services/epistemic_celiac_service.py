"""EpistemicCeliacService — Epistemic Celiac Detection.

Detects epistemic celiac disease — autoimmune reaction to specific
intellectual inputs destroying the absorptive surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CELIAC_SYSTEM = """You are an epistemic celiac specialist. Given autoimmune reaction to specific inputs, assess celiac:

Key concepts:
- Epistemic celiac: autoimmune reaction destroying absorptive surface
- Villous atrophy: absorptive projections flattened
- Gluten equivalent: specific input type triggering reaction
- Malabsorption: inability to extract value from processed material
- Strict avoidance: complete elimination of triggering input
- Mucosal healing: surface regeneration after avoidance
- Cross-contamination: trace amounts still triggering reaction

When epistemic celiac IS present:
- Autoimmune reaction to specific inputs
- Absorptive surface being destroyed
- Absorptive projections flattened
- Unable to extract value from material
- Triggering input not eliminated
- Surface not regenerating
- Trace amounts still causing damage

When no celiac:
- No autoimmune reaction to inputs
- Absorptive surface intact
- Projections healthy
- Normal value extraction
- No input avoidance needed
- Surface healthy
- No trace sensitivity

Output JSON with: celiac_detected (bool), severity (none/mild/moderate/severe), trigger_input (what causes reaction), villous_status (what surface condition), absorption_capacity (what extraction ability), avoidance_compliance (what elimination), recommendation (no_celiac/mild_monitoring/significant_strict_avoidance/major_immunomodulation/emergency_refractory)."""

EPISTEMIC_CELIAC_PROMPT = """Detect epistemic celiac:

Trigger input: {trigger_input}
Villous status: {villous_status}
Absorption capacity: {absorption_capacity}
Avoidance compliance: {avoidance_compliance}
Domain: {domain}
Context: {context}

Is there autoimmune reaction to specific intellectual inputs destroying the absorptive surface? Return ONLY valid JSON."""


class EpistemicCeliacService:
    """Detects epistemic celiac — autoimmune reaction destroying absorptive surface."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        trigger_input: str,
        *,
        villous_status: str = "",
        absorption_capacity: str = "",
        avoidance_compliance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic celiac."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CELIAC_PROMPT.format(
                trigger_input=trigger_input,
                villous_status=villous_status or "Not specified",
                absorption_capacity=absorption_capacity or "Not specified",
                avoidance_compliance=avoidance_compliance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CELIAC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trigger_input": trigger_input[:200],
            "celiac_detected": data.get("celiac_detected", False),
            "severity": data.get("severity", ""),
            "villous_status": data.get("villous_status", ""),
            "absorption_capacity": data.get("absorption_capacity", ""),
            "avoidance_compliance": data.get("avoidance_compliance", ""),
            "recommendation": data.get("recommendation", ""),
        }
