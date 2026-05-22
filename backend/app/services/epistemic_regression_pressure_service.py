"""EpistemicRegressionPressureService — Epistemic Regression Pressure Detection.

Detects epistemic regression pressure — pressure to regress to simpler
thinking patterns from social or emotional forces.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REGRESSION_PRESSURE_SYSTEM = """You are an epistemic regression pressure specialist. Given pressure to regress to simpler thinking, assess regression pressure:

Key concepts:
- Epistemic regression pressure: pressure to regress to simpler thinking
- Simplification demand: social demand to simplify one's thinking
- Anti-intellectual pressure: pressure to be less intellectual
- Dumbing down: pressure to dumb down one's analysis
- Group regression: group pulling thinking toward lowest common denominator
- Complexity punishment: being punished for complex thinking
- Sophistication shame: being shamed for sophisticated analysis

When epistemic regression pressure IS present:
- Pressure to regress to simpler thinking
- Social demand to simplify
- Pressure to be less intellectual
- Pressure to dumb down
- Group pulling toward lowest denominator
- Punished for complexity
- Shamed for sophistication

When no regression pressure:
- Free to think at full complexity
- No simplification demand
- Intellectual engagement welcomed
- Full analysis appreciated
- Group supports depth
- Complexity valued
- Sophistication respected

Output JSON with: regression_pressure_detected (bool), severity (none/mild/moderate/severe), simplification_demand (what demand to simplify), anti_intellectual_pressure (what pressure to be less intellectual), complexity_punishment (how punished for complexity), sophistication_shame (how shamed for sophistication), recommendation (no_regression_pressure/mild_boundary_setting/significant_environment_change/major_intensive_resistance_building/emergency_complete_regression_pressure)."""

EPISTEMIC_REGRESSION_PRESSURE_PROMPT = """Detect epistemic regression pressure:

Simplification demand: {simplification_demand}
Anti intellectual pressure: {anti_intellectual_pressure}
Complexity punishment: {complexity_punishment}
Sophistication shame: {sophistication_shame}
Domain: {domain}
Context: {context}

Is there pressure to regress to simpler thinking patterns? Return ONLY valid JSON."""


class EpistemicRegressionPressureService:
    """Detects epistemic regression pressure — pressure to regress to simpler thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        simplification_demand: str,
        *,
        anti_intellectual_pressure: str = "",
        complexity_punishment: str = "",
        sophistication_shame: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic regression pressure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REGRESSION_PRESSURE_PROMPT.format(
                simplification_demand=simplification_demand,
                anti_intellectual_pressure=anti_intellectual_pressure or "Not specified",
                complexity_punishment=complexity_punishment or "Not specified",
                sophistication_shame=sophistication_shame or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REGRESSION_PRESSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "simplification_demand": simplification_demand[:200],
            "regression_pressure_detected": data.get("regression_pressure_detected", False),
            "severity": data.get("severity", ""),
            "anti_intellectual_pressure": data.get("anti_intellectual_pressure", ""),
            "complexity_punishment": data.get("complexity_punishment", ""),
            "sophistication_shame": data.get("sophistication_shame", ""),
            "recommendation": data.get("recommendation", ""),
        }
