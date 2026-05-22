"""EpistemicSharedPsychosisService — Epistemic Shared Psychosis Detection.

Detects epistemic shared psychosis — transmission of delusional beliefs
from a dominant individual to closely associated others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SHARED_PSYCHOSIS_SYSTEM = """You are an epistemic shared psychosis specialist. Given transmitted delusional beliefs, assess shared psychosis:

Key concepts:
- Epistemic shared psychosis: delusion transmitted from dominant to others
- Inducer: dominant individual with primary delusion
- Induced: recipients who adopt the delusion
- Close association: proximity enabling transmission
- Isolation: cut off from reality-checking others
- Power differential: inducer has authority over induced
- Separation test: delusion fades when separated from inducer

When epistemic shared psychosis IS present:
- Delusion transmitted
- Dominant individual with primary belief
- Others adopting belief
- Close proximity
- Cut off from reality checks
- Authority differential
- Would fade if separated

When no shared psychosis:
- Independent beliefs
- No dominant inducer
- Own belief formation
- Diverse contacts
- Reality checks available
- Equal relationships
- Beliefs stable regardless

Output JSON with: shared_psychosis_detected (bool), severity (none/mild/moderate/severe), inducer_pattern (what dominant), induced_pattern (what adopting), isolation_level (what cut off), power_differential (what authority), recommendation (no_shared_psychosis/mild_separation_trial/significant_deprogramming/major_intensive_treatment/emergency_complete_induction)."""

EPISTEMIC_SHARED_PSYCHOSIS_PROMPT = """Detect epistemic shared psychosis:

Inducer pattern: {inducer_pattern}
Induced pattern: {induced_pattern}
Isolation level: {isolation_level}
Power differential: {power_differential}
Domain: {domain}
Context: {context}

Is there transmission of delusional beliefs from dominant individual to others? Return ONLY valid JSON."""


class EpistemicSharedPsychosisService:
    """Detects epistemic shared psychosis — transmitted delusional beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inducer_pattern: str,
        *,
        induced_pattern: str = "",
        isolation_level: str = "",
        power_differential: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic shared psychosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SHARED_PSYCHOSIS_PROMPT.format(
                inducer_pattern=inducer_pattern,
                induced_pattern=induced_pattern or "Not specified",
                isolation_level=isolation_level or "Not specified",
                power_differential=power_differential or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SHARED_PSYCHOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inducer_pattern": inducer_pattern[:200],
            "shared_psychosis_detected": data.get("shared_psychosis_detected", False),
            "severity": data.get("severity", ""),
            "induced_pattern": data.get("induced_pattern", ""),
            "isolation_level": data.get("isolation_level", ""),
            "power_differential": data.get("power_differential", ""),
            "recommendation": data.get("recommendation", ""),
        }
