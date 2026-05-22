"""EpistemicInfectionControlService — Epistemic Infection Control Detection.

Detects epistemic infection control failures — breakdown in measures
preventing spread of intellectual contamination.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFECTION_CONTROL_SYSTEM = """You are an epistemic infection control specialist. Given intellectual contamination spread, assess infection control:

Key concepts:
- Epistemic infection control: preventing intellectual contamination spread
- Hand hygiene: basic contamination prevention
- Isolation: separating contaminated from clean
- PPE: protective equipment against contamination
- Sterilization: complete elimination of contaminants
- Outbreak: uncontrolled spread of contamination
- Contact tracing: identifying exposure chain

When epistemic infection control IS failing:
- Contamination spreading unchecked
- Basic prevention not followed
- Contaminated not separated from clean
- No protective measures in place
- Incomplete elimination of contaminants
- Uncontrolled spread occurring
- Exposure chain unknown

When infection control adequate:
- No contamination spread
- Basic prevention followed
- Proper separation maintained
- Protective measures in place
- Complete sterilization achieved
- Controlled environment
- Exposure chain tracked

Output JSON with: infection_control_failure (bool), severity (none/mild/moderate/severe), breach_type (what prevention failure), spread_pattern (what contamination path), isolation_status (what separation), outbreak_risk (what uncontrolled spread), recommendation (no_failure_detected/mild_reinforcement/significant_intervention/major_outbreak_response/emergency_containment)."""

EPISTEMIC_INFECTION_CONTROL_PROMPT = """Detect epistemic infection control failure:

Breach type: {breach_type}
Spread pattern: {spread_pattern}
Isolation status: {isolation_status}
Outbreak risk: {outbreak_risk}
Domain: {domain}
Context: {context}

Are measures preventing intellectual contamination spread failing? Return ONLY valid JSON."""


class EpistemicInfectionControlService:
    """Detects epistemic infection control failures — contamination spread prevention."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        breach_type: str,
        *,
        spread_pattern: str = "",
        isolation_status: str = "",
        outbreak_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic infection control failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFECTION_CONTROL_PROMPT.format(
                breach_type=breach_type,
                spread_pattern=spread_pattern or "Not specified",
                isolation_status=isolation_status or "Not specified",
                outbreak_risk=outbreak_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFECTION_CONTROL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "breach_type": breach_type[:200],
            "infection_control_failure": data.get("infection_control_failure", False),
            "severity": data.get("severity", ""),
            "spread_pattern": data.get("spread_pattern", ""),
            "isolation_status": data.get("isolation_status", ""),
            "outbreak_risk": data.get("outbreak_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
