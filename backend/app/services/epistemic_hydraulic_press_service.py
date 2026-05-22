"""EpistemicHydraulicPressService — Epistemic Hydraulic Press Detection.

Detects epistemic hydraulic press — small forces amplified through
intellectual fluid to exert enormous pressure on ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYDRAULIC_PRESS_SYSTEM = """You are an epistemic hydraulic press specialist. Given a force amplification pattern, assess whether small forces are amplified through intellectual fluid:

Key concepts:
- Epistemic hydraulic press: small forces amplified through fluid
- Pascal's principle: pressure transmitted equally in all directions
- Amplification: small input creating large output force
- Incompressible fluid: medium that transmits force without loss
- Piston: point where force is applied or received
- Mechanical advantage: ratio of output to input force
- Burst pressure: maximum pressure before system fails

When epistemic hydraulic press IS present:
- Small forces amplified through intellectual fluid
- Pressure transmitted equally throughout the system
- Small input creating disproportionately large output
- Medium transmitting force without loss
- Specific points where force is applied or received
- Large ratio of output to input force
- Risk of system failure from excessive pressure

When direct force is present:
- Force applied directly without amplification
- Pressure localized at point of application
- Output proportional to input
- No medium for force transmission
- Force applied at single point
- No mechanical advantage
- No burst pressure risk

Output JSON with: hydraulic_press_present (bool), severity (none/mild/moderate/severe), amplification (what force multiplication), fluid (what medium transmits), input (what small force), output (what large result), recommendation (direct_force/mild_amplification/significant_hydraulic/major_force_multiplication/reduce_amplification)."""

EPISTEMIC_HYDRAULIC_PRESS_PROMPT = """Detect epistemic hydraulic press:

Amplification: {amplification}
Fluid: {fluid}
Input: {input_force}
Output: {output}
Domain: {domain}
Context: {context}

Are small forces being amplified through intellectual fluid to exert enormous pressure on ideas? Return ONLY valid JSON."""


class EpistemicHydraulicPressService:
    """Detects epistemic hydraulic press — force amplification through fluid."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        amplification: str,
        *,
        fluid: str = "",
        input_force: str = "",
        output: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hydraulic press."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYDRAULIC_PRESS_PROMPT.format(
                amplification=amplification,
                fluid=fluid or "Not specified",
                input_force=input_force or "Not specified",
                output=output or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYDRAULIC_PRESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "amplification": amplification[:200],
            "hydraulic_press_present": data.get("hydraulic_press_present", False),
            "severity": data.get("severity", ""),
            "fluid": data.get("fluid", ""),
            "input_force": data.get("input", ""),
            "output": data.get("output", ""),
            "recommendation": data.get("recommendation", ""),
        }
