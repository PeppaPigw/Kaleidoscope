"""EpistemicConductiveLossService — Epistemic Conductive Loss Detection.

Detects epistemic conductive loss — mechanical blockage preventing
intellectual signals from reaching processing centers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONDUCTIVE_LOSS_SYSTEM = """You are an epistemic conductive loss specialist. Given mechanical intellectual signal blockage, assess conductive loss:

Key concepts:
- Epistemic conductive loss: mechanical blockage of signal transmission
- Ossicular fixation: transmission chain frozen
- Tympanic perforation: receiving membrane damaged
- Cerumen impaction: buildup blocking signal path
- Otosclerosis: abnormal bone growth fixing chain
- Air-bone gap: difference between potential and actual reception
- Surgical correction: physically removing blockage

When epistemic conductive loss IS present:
- Mechanical blockage preventing signal transmission
- Transmission chain frozen or damaged
- Receiving membrane perforated
- Buildup blocking signal path
- Abnormal growth fixing transmission
- Gap between potential and actual reception
- Physical removal of blockage needed

When no conductive loss:
- Clear signal transmission path
- Transmission chain mobile
- Receiving membrane intact
- No buildup present
- Normal growth patterns
- No air-bone gap
- No surgical intervention needed

Output JSON with: conductive_loss_detected (bool), severity (none/mild/moderate/severe), blockage_type (what obstruction), transmission_status (what chain condition), air_bone_gap (what reception difference), correction_feasibility (what removal possibility), recommendation (no_conductive_loss/mild_cerumen_removal/significant_medical_treatment/major_surgical_correction/emergency_acute_perforation)."""

EPISTEMIC_CONDUCTIVE_LOSS_PROMPT = """Detect epistemic conductive loss:

Blockage type: {blockage_type}
Transmission status: {transmission_status}
Air-bone gap: {air_bone_gap}
Correction feasibility: {correction_feasibility}
Domain: {domain}
Context: {context}

Is there mechanical blockage preventing intellectual signals from reaching processing? Return ONLY valid JSON."""


class EpistemicConductiveLossService:
    """Detects epistemic conductive loss — mechanical blockage of signal transmission."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        blockage_type: str,
        *,
        transmission_status: str = "",
        air_bone_gap: str = "",
        correction_feasibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conductive loss."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONDUCTIVE_LOSS_PROMPT.format(
                blockage_type=blockage_type,
                transmission_status=transmission_status or "Not specified",
                air_bone_gap=air_bone_gap or "Not specified",
                correction_feasibility=correction_feasibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONDUCTIVE_LOSS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "blockage_type": blockage_type[:200],
            "conductive_loss_detected": data.get("conductive_loss_detected", False),
            "severity": data.get("severity", ""),
            "transmission_status": data.get("transmission_status", ""),
            "air_bone_gap": data.get("air_bone_gap", ""),
            "correction_feasibility": data.get("correction_feasibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
