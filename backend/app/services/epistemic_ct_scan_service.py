"""EpistemicCtScanService — Epistemic CT Scan Detection.

Detects need for epistemic CT scan — cross-sectional imaging revealing
intellectual layers and their internal composition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CT_SCAN_SYSTEM = """You are an epistemic CT scan specialist. Given intellectual layers, assess whether cross-sectional pathology exists:

Key concepts:
- Epistemic CT scan: cross-sectional imaging of intellectual layers
- Density abnormality: areas denser or less dense than normal
- Calcification: hardened deposits within soft tissue
- Fluid collection: accumulated liquid in abnormal location
- Fracture line: break in intellectual framework
- Contrast enhancement: areas with increased blood supply
- Incidental finding: unexpected pathology discovered

When epistemic CT scan findings ARE present:
- Cross-sectional pathology in intellectual layers
- Areas abnormally dense or hollow
- Hardened deposits in soft intellectual tissue
- Accumulated fluid in wrong locations
- Breaks in intellectual framework
- Areas with abnormal activity supply
- Unexpected pathology discovered incidentally

When healthy layers are present:
- Normal cross-sectional appearance
- Uniform appropriate density
- No calcifications
- No fluid collections
- Intact framework
- Normal activity distribution
- No incidental findings

Output JSON with: ct_findings_present (bool), severity (none/mild/moderate/severe), density_abnormality (what density change), calcification (what hardened deposits), fluid_collection (what accumulated liquid), fracture_line (what framework break), recommendation (healthy_layers/mild_findings/significant_cross_sectional_pathology/major_layer_disease/address_intellectual_layer_pathology)."""

EPISTEMIC_CT_SCAN_PROMPT = """Detect epistemic CT scan findings:

Density abnormality: {density_abnormality}
Calcification: {calcification}
Fluid collection: {fluid_collection}
Fracture line: {fracture_line}
Domain: {domain}
Context: {context}

Is there cross-sectional pathology within intellectual layers? Return ONLY valid JSON."""


class EpistemicCtScanService:
    """Detects epistemic CT scan findings — cross-sectional intellectual pathology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        density_abnormality: str,
        *,
        calcification: str = "",
        fluid_collection: str = "",
        fracture_line: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic CT scan findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CT_SCAN_PROMPT.format(
                density_abnormality=density_abnormality,
                calcification=calcification or "Not specified",
                fluid_collection=fluid_collection or "Not specified",
                fracture_line=fracture_line or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CT_SCAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "density_abnormality": density_abnormality[:200],
            "ct_findings_present": data.get("ct_findings_present", False),
            "severity": data.get("severity", ""),
            "calcification": data.get("calcification", ""),
            "fluid_collection": data.get("fluid_collection", ""),
            "fracture_line": data.get("fracture_line", ""),
            "recommendation": data.get("recommendation", ""),
        }
