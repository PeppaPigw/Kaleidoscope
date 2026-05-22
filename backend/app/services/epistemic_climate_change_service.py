"""EpistemicClimateChangeService — Epistemic Climate Change Detection.

Detects epistemic climate change — gradual long-term shifts in
intellectual environment that alter conditions for all ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CLIMATE_CHANGE_SYSTEM = """You are an epistemic climate change specialist. Given an intellectual environment, assess whether gradual long-term shifts are altering conditions:

Key concepts:
- Epistemic climate change: gradual long-term intellectual shifts
- Environmental alteration: intellectual environment changing
- Condition shift: conditions for ideas changing
- Gradual transformation: slow but fundamental transformation
- Adaptation pressure: pressure to adapt to new conditions
- Extinction risk: ideas unable to adapt facing extinction
- New normal: establishment of fundamentally different conditions

When epistemic climate change IS present:
- Gradual long-term shifts altering intellectual environment
- Intellectual environment fundamentally changing
- Conditions for ideas changing over time
- Slow but fundamental transformation occurring
- Pressure to adapt to new intellectual conditions
- Ideas unable to adapt facing extinction
- Fundamentally different conditions becoming normal

When stable environment is present:
- Intellectual environment relatively stable
- Conditions for ideas consistent
- No fundamental transformation occurring
- No unusual adaptation pressure
- Ideas viable in current conditions
- Environment supporting existing approaches
- Conditions within normal variation

Output JSON with: climate_change_present (bool), severity (none/mild/moderate/severe), environment (what environment is shifting), shift (what shift is occurring), timeline (how gradual the change), adaptation (what adaptation is needed), recommendation (stable_environment/mild_shift/significant_climate_change/major_environmental_transformation/adapt_to_new_conditions)."""

EPISTEMIC_CLIMATE_CHANGE_PROMPT = """Detect epistemic climate change:

Environment: {environment}
Shift: {shift}
Timeline: {timeline}
Adaptation: {adaptation}
Domain: {domain}
Context: {context}

Are gradual long-term shifts altering the intellectual environment? Return ONLY valid JSON."""


class EpistemicClimateChangeService:
    """Detects epistemic climate change — gradual long-term intellectual shifts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        shift: str = "",
        timeline: str = "",
        adaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic climate change."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CLIMATE_CHANGE_PROMPT.format(
                environment=environment,
                shift=shift or "Not specified",
                timeline=timeline or "Not specified",
                adaptation=adaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CLIMATE_CHANGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "climate_change_present": data.get("climate_change_present", False),
            "severity": data.get("severity", ""),
            "shift": data.get("shift", ""),
            "timeline": data.get("timeline", ""),
            "adaptation": data.get("adaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }
