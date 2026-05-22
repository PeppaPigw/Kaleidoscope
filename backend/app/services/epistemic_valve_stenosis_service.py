"""EpistemicValveStenosisService — Epistemic Valve Stenosis Detection.

Detects epistemic valve stenosis — narrowed gates restricting idea flow,
where intellectual checkpoints become bottlenecks.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VALVE_STENOSIS_SYSTEM = """You are an epistemic valve stenosis specialist. Given intellectual gates, assess whether they have narrowed to restrict idea flow:

Key concepts:
- Epistemic valve stenosis: narrowed gates restricting idea flow
- Valve calcification: gate becoming rigid and narrow
- Pressure gradient: buildup of pressure before the restriction
- Regurgitation: backflow through incompetent valve
- Turbulent flow: disrupted flow pattern through narrow opening
- Compensatory hypertrophy: upstream system working harder
- Decompensation: system failing despite compensation

When epistemic valve stenosis IS present:
- Gates narrowed restricting idea flow
- Intellectual checkpoints becoming rigid and narrow
- Pressure building up before restrictions
- Ideas flowing backward through incompetent gates
- Disrupted flow patterns through narrow openings
- Upstream systems working harder to compensate
- System failing despite compensatory efforts

When healthy valves are present:
- Gates open fully for idea flow
- Flexible responsive checkpoints
- No pressure buildup
- No backflow
- Smooth laminar flow
- Normal workload distribution
- System functioning efficiently

Output JSON with: valve_stenosis_present (bool), severity (none/mild/moderate/severe), valve_calcification (what rigidity), pressure_gradient (what buildup), regurgitation (what backflow), compensatory_hypertrophy (what overwork), recommendation (healthy_valves/mild_stenosis/significant_valve_stenosis/major_gate_restriction/open_intellectual_gates)."""

EPISTEMIC_VALVE_STENOSIS_PROMPT = """Detect epistemic valve stenosis:

Valve calcification: {valve_calcification}
Pressure gradient: {pressure_gradient}
Regurgitation: {regurgitation}
Compensatory hypertrophy: {compensatory_hypertrophy}
Domain: {domain}
Context: {context}

Have intellectual gates narrowed to restrict idea flow, creating bottlenecks? Return ONLY valid JSON."""


class EpistemicValveStenosisService:
    """Detects epistemic valve stenosis — narrowed gates restricting idea flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        valve_calcification: str,
        *,
        pressure_gradient: str = "",
        regurgitation: str = "",
        compensatory_hypertrophy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic valve stenosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VALVE_STENOSIS_PROMPT.format(
                valve_calcification=valve_calcification,
                pressure_gradient=pressure_gradient or "Not specified",
                regurgitation=regurgitation or "Not specified",
                compensatory_hypertrophy=compensatory_hypertrophy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VALVE_STENOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "valve_calcification": valve_calcification[:200],
            "valve_stenosis_present": data.get("valve_stenosis_present", False),
            "severity": data.get("severity", ""),
            "pressure_gradient": data.get("pressure_gradient", ""),
            "regurgitation": data.get("regurgitation", ""),
            "compensatory_hypertrophy": data.get("compensatory_hypertrophy", ""),
            "recommendation": data.get("recommendation", ""),
        }
