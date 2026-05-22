"""EpistemicShockManagementService — Epistemic Shock Management Detection.

Detects need for epistemic shock management — treating intellectual
circulatory collapse where vital reasoning organs are not receiving
adequate perfusion.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHOCK_SYSTEM = """You are an epistemic shock management specialist. Given intellectual circulatory collapse, assess whether shock management is needed:

Key concepts:
- Epistemic shock: intellectual circulatory collapse
- Hypovolemic: shock from intellectual substance loss
- Cardiogenic: shock from intellectual pump failure
- Distributive: shock from intellectual vessel dilation
- Obstructive: shock from intellectual flow blockage
- Perfusion: delivery of intellectual substance to organs
- Vasopressors: agents to maintain intellectual pressure

When epistemic shock management IS needed:
- Intellectual circulatory collapse present
- Vital reasoning organs underperfused
- Intellectual substance loss causing shock
- Intellectual pump failure present
- Intellectual vessel dilation causing collapse
- Intellectual flow blockage present
- Need for agents to maintain pressure

When no shock management needed:
- Normal intellectual circulation
- Adequate organ perfusion
- No substance loss
- Normal pump function
- Normal vessel tone
- No flow blockage
- Stable intellectual pressure

Output JSON with: shock_management_needed (bool), severity (none/mild/moderate/severe), shock_type (what category), perfusion_status (what delivery state), fluid_status (what volume state), vasopressor_need (what pressure support), recommendation (no_shock_management_needed/mild_fluid_bolus/significant_resuscitation/major_vasopressor_support/emergency_massive_transfusion)."""

EPISTEMIC_SHOCK_PROMPT = """Detect epistemic shock management need:

Shock type: {shock_type}
Perfusion status: {perfusion_status}
Fluid status: {fluid_status}
Vasopressor need: {vasopressor_need}
Domain: {domain}
Context: {context}

Is intellectual circulatory collapse present requiring shock management? Return ONLY valid JSON."""


class EpistemicShockManagementService:
    """Detects epistemic shock management need — treating intellectual circulatory collapse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shock_type: str,
        *,
        perfusion_status: str = "",
        fluid_status: str = "",
        vasopressor_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic shock management need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHOCK_PROMPT.format(
                shock_type=shock_type,
                perfusion_status=perfusion_status or "Not specified",
                fluid_status=fluid_status or "Not specified",
                vasopressor_need=vasopressor_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHOCK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shock_type": shock_type[:200],
            "shock_management_needed": data.get("shock_management_needed", False),
            "severity": data.get("severity", ""),
            "perfusion_status": data.get("perfusion_status", ""),
            "fluid_status": data.get("fluid_status", ""),
            "vasopressor_need": data.get("vasopressor_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
