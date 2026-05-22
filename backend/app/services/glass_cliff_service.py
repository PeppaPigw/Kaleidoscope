"""GlassCliffService — Glass Cliff Detection.

Detects glass cliff — appointing people (often from underrepresented
groups) to leadership positions during crises or in situations
likely to fail, setting them up for failure and then attributing
the failure to their characteristics rather than the impossible
situation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

GLASS_CLIFF_SYSTEM = """You are a glass cliff specialist. Given a leadership appointment or assignment, assess whether someone is being set up for failure:

Key concepts:
- Glass cliff: precarious leadership positions during crisis
- Setup for failure: impossible situations presented as opportunities
- Scapegoating: blaming the appointee for pre-existing problems
- Token appointment: diversity hire into a doomed role
- Poisoned chalice: role that appears prestigious but is designed to fail
- Structural constraints: limitations that make success impossible
- Attribution error: blaming individual for systemic failure

When glass cliff IS present:
- Appointment to leadership during an already-failing situation
- Insufficient resources or authority to succeed
- Previous leaders left or were removed due to the same problems
- The appointee is from an underrepresented group in a crisis role
- Success criteria are unrealistic given constraints
- Blame is likely to fall on the individual, not the situation
- The role has a history of rapid turnover

When glass cliff is NOT present:
- The appointment comes with adequate resources and authority
- The situation is challenging but not pre-determined to fail
- The appointee has genuine support and realistic expectations
- Success criteria are achievable given the constraints
- The appointment is based on relevant qualifications
- Previous holders of the role had similar support levels
- Structural problems are acknowledged as systemic, not individual

Output JSON with: glass_cliff_present (bool), severity (none/mild/moderate/severe), appointment (who is being appointed to what), crisis_context (what crisis exists), resources (what support is provided), success_probability (realistic chance of success), attribution_risk (will failure be blamed on individual), recommendation (no_glass_cliff/mild_risk/significant_glass_cliff/major_setup_for_failure/ensure_adequate_support)."""

GLASS_CLIFF_PROMPT = """Detect glass cliff:

Situation: {situation}
Appointment: {appointment}
Crisis context: {crisis}
Resources provided: {resources}
Domain: {domain}
Context: {context}

Is someone being appointed to a leadership position set up for failure? Return ONLY valid JSON."""


class GlassCliffService:
    """Detects glass cliff — leadership appointments set up for failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        appointment: str = "",
        crisis: str = "",
        resources: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect glass cliff."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GLASS_CLIFF_PROMPT.format(
                situation=situation,
                appointment=appointment or "Not specified",
                crisis=crisis or "Not specified",
                resources=resources or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=GLASS_CLIFF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "glass_cliff_present": data.get("glass_cliff_present", False),
            "severity": data.get("severity", ""),
            "appointment": data.get("appointment", ""),
            "crisis_context": data.get("crisis_context", ""),
            "success_probability": data.get("success_probability", ""),
            "recommendation": data.get("recommendation", ""),
        }
