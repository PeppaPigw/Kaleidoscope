"""EpistemicDysphagiaService — Epistemic Dysphagia Detection.

Detects epistemic dysphagia — difficulty swallowing new intellectual
material, getting stuck in transit between intake and processing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DYSPHAGIA_SYSTEM = """You are an epistemic dysphagia specialist. Given difficulty swallowing intellectual material, assess dysphagia:

Key concepts:
- Epistemic dysphagia: difficulty swallowing new material
- Oropharyngeal: difficulty initiating the swallow
- Esophageal: material getting stuck in transit
- Mechanical obstruction: physical blockage in path
- Motility disorder: propulsion mechanism failing
- Aspiration risk: material going to wrong destination
- Modified diet: adapting input consistency

When epistemic dysphagia IS present:
- Difficulty swallowing new material
- Unable to initiate intake
- Material getting stuck in transit
- Physical blockage in path
- Propulsion mechanism failing
- Material going to wrong destination
- Input consistency needs modification

When no dysphagia:
- Material swallowed easily
- Intake initiated smoothly
- No transit obstruction
- Clear path
- Normal propulsion
- Material reaching correct destination
- Normal input consistency tolerated

Output JSON with: dysphagia_detected (bool), severity (none/mild/moderate/severe), swallow_phase (what stage affected), obstruction_type (what blockage), motility_status (what propulsion), aspiration_risk (what misdirection), recommendation (no_dysphagia/mild_texture_modification/significant_swallow_therapy/major_dilation_procedure/emergency_complete_obstruction)."""

EPISTEMIC_DYSPHAGIA_PROMPT = """Detect epistemic dysphagia:

Swallow phase: {swallow_phase}
Obstruction type: {obstruction_type}
Motility status: {motility_status}
Aspiration risk: {aspiration_risk}
Domain: {domain}
Context: {context}

Is there difficulty swallowing new intellectual material getting stuck in transit? Return ONLY valid JSON."""


class EpistemicDysphagiaService:
    """Detects epistemic dysphagia — difficulty swallowing new material."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        swallow_phase: str,
        *,
        obstruction_type: str = "",
        motility_status: str = "",
        aspiration_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dysphagia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DYSPHAGIA_PROMPT.format(
                swallow_phase=swallow_phase,
                obstruction_type=obstruction_type or "Not specified",
                motility_status=motility_status or "Not specified",
                aspiration_risk=aspiration_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DYSPHAGIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "swallow_phase": swallow_phase[:200],
            "dysphagia_detected": data.get("dysphagia_detected", False),
            "severity": data.get("severity", ""),
            "obstruction_type": data.get("obstruction_type", ""),
            "motility_status": data.get("motility_status", ""),
            "aspiration_risk": data.get("aspiration_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
