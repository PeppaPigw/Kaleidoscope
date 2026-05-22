"""DisplacementEffectService — Displacement Effect Detection.

Identifies when solving a problem in one place merely displaces it
to another location, time, or form. Like squeezing a balloon —
the volume doesn't change, it just moves. Crime displacement,
pollution displacement, risk displacement — the problem doesn't
disappear, it just relocates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISPLACEMENT_SYSTEM = """You are a displacement effect specialist. Given an intervention and its claimed success, assess whether the problem was actually solved or merely displaced:
- Did the problem move to a different location?
- Did it move to a different time (delayed rather than prevented)?
- Did it change form (different manifestation of the same underlying issue)?
- Did it move to a different population (affecting someone else instead)?
- Is the net effect actually zero or negative when displacement is accounted for?

Output JSON with: displacement_detected (bool), severity (none/mild/moderate/severe), intervention (what was done), claimed_success (what improvement is claimed), displacement_type (spatial/temporal/form/population/system/none), where_displaced_to (where the problem moved), who_now_bears_it (who is affected after displacement), net_effect (positive/neutral/negative — overall impact including displacement), visibility_asymmetry (bool — is the displacement less visible than the original problem?), measurement_bias (bool — are we measuring where the intervention happened but not where the problem moved?), balloon_squeeze (bool — is this a fixed-quantity problem that can only be redistributed?), underlying_cause_addressed (bool — was the root cause fixed or just the symptom moved?), displacement_chain (list of: from, to, mechanism), total_system_impact (better/same/worse when all displacement is counted), who_benefits_from_displacement (who gains from the problem being less visible even if not solved), recommendation (genuine_solution/acknowledge_displacement/address_root_cause/measure_system_wide/accept_tradeoff)."""

DISPLACEMENT_PROMPT = """Detect displacement effects:

Intervention: {intervention}
Claimed success: {claimed_success}
System boundary: {system_boundary}
What to look for: {look_for}
Domain: {domain}
Context: {context}

Was the problem displaced rather than solved? Return ONLY valid JSON."""


class DisplacementEffectService:
    """Detects displacement effects — problems moved rather than solved."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intervention: str,
        *,
        claimed_success: str = "",
        system_boundary: str = "",
        look_for: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect displacement effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISPLACEMENT_PROMPT.format(
                intervention=intervention,
                claimed_success=claimed_success or "Not specified",
                system_boundary=system_boundary or "Not specified",
                look_for=look_for or "Any displacement",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISPLACEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intervention": intervention[:200],
            "displacement_detected": data.get("displacement_detected", False),
            "severity": data.get("severity", ""),
            "displacement_type": data.get("displacement_type", ""),
            "where_displaced_to": data.get("where_displaced_to", ""),
            "who_now_bears_it": data.get("who_now_bears_it", ""),
            "net_effect": data.get("net_effect", ""),
            "visibility_asymmetry": data.get("visibility_asymmetry", False),
            "measurement_bias": data.get("measurement_bias", False),
            "balloon_squeeze": data.get("balloon_squeeze", False),
            "underlying_cause_addressed": data.get("underlying_cause_addressed", False),
            "displacement_chain": data.get("displacement_chain", []),
            "total_system_impact": data.get("total_system_impact", ""),
            "who_benefits_from_displacement": data.get("who_benefits_from_displacement", ""),
            "recommendation": data.get("recommendation", ""),
        }
