"""EpistemicEnvironmentPressureService — Epistemic Environment Pressure Detection.

Detects epistemic environment pressure — environmental pressures rushing
epistemic processes and forcing premature conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENVIRONMENT_PRESSURE_SYSTEM = """You are an epistemic environment pressure specialist. Given environmental pressures rushing epistemic processes, assess environment pressure:

Key concepts:
- Epistemic environment pressure: environmental pressures rushing epistemic processes
- Deadline pressure: deadlines forcing premature conclusions
- Productivity pressure: productivity demands rushing thinking
- Output pressure: pressure to produce output over quality
- Speed over depth: environment valuing speed over depth
- Throughput demand: demand for throughput over understanding
- Urgency manufacture: manufactured urgency rushing judgment

When epistemic environment pressure IS present:
- Environment pressuring rushing
- Deadlines forcing premature conclusions
- Productivity rushing thinking
- Output pressured over quality
- Speed valued over depth
- Throughput demanded over understanding
- Urgency manufactured

When no environment pressure:
- Environment supporting pace
- Deadlines reasonable
- Productivity balanced with quality
- Quality valued
- Depth valued
- Understanding valued
- Urgency genuine

Output JSON with: environment_pressure_detected (bool), severity (none/mild/moderate/severe), deadline_pressure (what deadlines forcing), productivity_pressure (what productivity rushing), output_pressure (what output pressured over quality), speed_over_depth (what speed valued over depth), recommendation (no_environment_pressure/mild_pace_protection/significant_depth_recovery/major_intensive_pressure_resistance/emergency_complete_environment_pressure)."""

EPISTEMIC_ENVIRONMENT_PRESSURE_PROMPT = """Detect epistemic environment pressure:

Deadline pressure: {deadline_pressure}
Productivity pressure: {productivity_pressure}
Output pressure: {output_pressure}
Speed over depth: {speed_over_depth}
Domain: {domain}
Context: {context}

Are environmental pressures rushing epistemic processes? Return ONLY valid JSON."""


class EpistemicEnvironmentPressureService:
    """Detects epistemic environment pressure — pressures rushing processes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deadline_pressure: str,
        *,
        productivity_pressure: str = "",
        output_pressure: str = "",
        speed_over_depth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic environment pressure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENVIRONMENT_PRESSURE_PROMPT.format(
                deadline_pressure=deadline_pressure,
                productivity_pressure=productivity_pressure or "Not specified",
                output_pressure=output_pressure or "Not specified",
                speed_over_depth=speed_over_depth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENVIRONMENT_PRESSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deadline_pressure": deadline_pressure[:200],
            "environment_pressure_detected": data.get("environment_pressure_detected", False),
            "severity": data.get("severity", ""),
            "productivity_pressure": data.get("productivity_pressure", ""),
            "output_pressure": data.get("output_pressure", ""),
            "speed_over_depth": data.get("speed_over_depth", ""),
            "recommendation": data.get("recommendation", ""),
        }
