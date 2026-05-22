"""EpistemicAirwayManagementService — Epistemic Airway Management Detection.

Detects need for epistemic airway management — ensuring intellectual
breathing pathways remain open and functional.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AIRWAY_SYSTEM = """You are an epistemic airway management specialist. Given intellectual breathing difficulties, assess whether airway intervention is needed:

Key concepts:
- Epistemic airway: the pathway through which intellectual input flows
- Obstruction: blockage preventing intellectual intake
- Intubation: inserting artificial pathway to maintain flow
- Aspiration: foreign material entering intellectual lungs
- Ventilation: mechanical assistance for intellectual breathing
- Tracheostomy: creating alternative pathway when normal blocked
- Oxygen saturation: adequacy of intellectual nourishment

When epistemic airway management IS needed:
- Intellectual intake pathway obstructed
- Normal breathing of ideas compromised
- Need for artificial pathway insertion
- Foreign material contaminating intake
- Mechanical assistance required
- Alternative pathway needed
- Intellectual nourishment inadequate

When no airway management needed:
- Clear intellectual intake pathway
- Normal idea breathing
- No obstruction present
- No contamination risk
- Self-sustaining ventilation
- Normal pathway functional
- Adequate intellectual nourishment

Output JSON with: airway_management_needed (bool), severity (none/mild/moderate/severe), obstruction_type (what blocking), ventilation_status (what breathing state), aspiration_risk (what contamination), intervention_type (what needed), recommendation (no_airway_management_needed/mild_positioning/significant_intervention/major_intubation/emergency_surgical_airway)."""

EPISTEMIC_AIRWAY_PROMPT = """Detect epistemic airway management need:

Obstruction type: {obstruction_type}
Ventilation status: {ventilation_status}
Aspiration risk: {aspiration_risk}
Intervention type: {intervention_type}
Domain: {domain}
Context: {context}

Is the intellectual intake pathway compromised and needing intervention? Return ONLY valid JSON."""


class EpistemicAirwayManagementService:
    """Detects epistemic airway management need — ensuring intellectual breathing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        obstruction_type: str,
        *,
        ventilation_status: str = "",
        aspiration_risk: str = "",
        intervention_type: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic airway management need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AIRWAY_PROMPT.format(
                obstruction_type=obstruction_type,
                ventilation_status=ventilation_status or "Not specified",
                aspiration_risk=aspiration_risk or "Not specified",
                intervention_type=intervention_type or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AIRWAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "obstruction_type": obstruction_type[:200],
            "airway_management_needed": data.get("airway_management_needed", False),
            "severity": data.get("severity", ""),
            "ventilation_status": data.get("ventilation_status", ""),
            "aspiration_risk": data.get("aspiration_risk", ""),
            "intervention_type": data.get("intervention_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
