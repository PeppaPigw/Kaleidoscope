"""EpistemicCesareanService — Epistemic Cesarean Detection.

Detects need for epistemic cesarean — surgical delivery of an intellectual
creation when natural birth pathway is obstructed or dangerous.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CESAREAN_SYSTEM = """You are an epistemic cesarean specialist. Given obstructed intellectual birth, assess cesarean need:

Key concepts:
- Epistemic cesarean: surgical delivery bypassing natural pathway
- Cephalopelvic disproportion: creation too large for pathway
- Fetal distress: creation in danger during labor
- Placenta previa: pathway blocked by support structure
- Cord prolapse: lifeline compressed during delivery
- Repeat cesarean: prior surgical delivery requiring another
- VBAC: attempting natural after prior surgical

When epistemic cesarean IS needed:
- Natural pathway obstructed
- Creation too large for pathway
- Creation in danger during labor
- Support structure blocking pathway
- Lifeline compressed during delivery
- Prior surgical delivery complicating
- Natural attempt after surgical failing

When no cesarean needed:
- Natural pathway clear
- Creation fits pathway
- Creation not in danger
- No pathway obstruction
- Lifeline intact
- No prior surgical complications
- Natural delivery progressing

Output JSON with: cesarean_needed (bool), severity (none/mild/moderate/severe), obstruction_type (what blocking), distress_signs (what danger), pathway_status (what route condition), urgency_category (what time pressure), recommendation (no_cesarean_needed/mild_monitoring/significant_planned_cesarean/major_urgent_cesarean/emergency_crash_cesarean)."""

EPISTEMIC_CESAREAN_PROMPT = """Detect epistemic cesarean need:

Obstruction type: {obstruction_type}
Distress signs: {distress_signs}
Pathway status: {pathway_status}
Urgency category: {urgency_category}
Domain: {domain}
Context: {context}

Is the natural intellectual birth pathway obstructed requiring surgical delivery? Return ONLY valid JSON."""


class EpistemicCesareanService:
    """Detects epistemic cesarean need — surgical delivery when natural path blocked."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        obstruction_type: str,
        *,
        distress_signs: str = "",
        pathway_status: str = "",
        urgency_category: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cesarean need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CESAREAN_PROMPT.format(
                obstruction_type=obstruction_type,
                distress_signs=distress_signs or "Not specified",
                pathway_status=pathway_status or "Not specified",
                urgency_category=urgency_category or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CESAREAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "obstruction_type": obstruction_type[:200],
            "cesarean_needed": data.get("cesarean_needed", False),
            "severity": data.get("severity", ""),
            "distress_signs": data.get("distress_signs", ""),
            "pathway_status": data.get("pathway_status", ""),
            "urgency_category": data.get("urgency_category", ""),
            "recommendation": data.get("recommendation", ""),
        }
