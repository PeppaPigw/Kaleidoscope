"""EpistemicPeriodontalDiseaseService — Epistemic Periodontal Disease Detection.

Detects epistemic periodontal disease — deterioration of the supporting
structures around intellectual concepts, threatening their stability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERIODONTAL_SYSTEM = """You are an epistemic periodontal disease specialist. Given deterioration of intellectual support structures, assess:

Key concepts:
- Epistemic periodontal disease: support structure deterioration
- Gingivitis: early inflammation of support tissue
- Periodontitis: advanced destruction of support
- Bone loss: loss of deep structural support
- Pocket depth: gap between concept and support
- Scaling: removing buildup from support surface
- Tooth mobility: concept loosening from lost support

When epistemic periodontal disease IS present:
- Support structures deteriorating
- Early inflammation of support tissue
- Advanced destruction occurring
- Deep structural support lost
- Gap between concept and support widening
- Buildup on support surfaces
- Concepts loosening from lost support

When no periodontal disease:
- Support structures healthy
- No inflammation
- No destruction
- Deep support intact
- No gaps present
- Clean support surfaces
- Concepts firmly supported

Output JSON with: periodontal_disease (bool), severity (none/mild/moderate/severe), inflammation_status (what tissue state), bone_loss_extent (what structural loss), pocket_depth (what gap measurement), mobility_grade (what loosening), recommendation (no_periodontal_disease/mild_gingivitis/significant_early_periodontitis/major_advanced_periodontitis/emergency_acute_periodontal_abscess)."""

EPISTEMIC_PERIODONTAL_PROMPT = """Detect epistemic periodontal disease:

Inflammation status: {inflammation_status}
Bone loss extent: {bone_loss_extent}
Pocket depth: {pocket_depth}
Mobility grade: {mobility_grade}
Domain: {domain}
Context: {context}

Are the supporting structures around intellectual concepts deteriorating? Return ONLY valid JSON."""


class EpistemicPeriodontalDiseaseService:
    """Detects epistemic periodontal disease — support structure deterioration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inflammation_status: str,
        *,
        bone_loss_extent: str = "",
        pocket_depth: str = "",
        mobility_grade: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic periodontal disease."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERIODONTAL_PROMPT.format(
                inflammation_status=inflammation_status,
                bone_loss_extent=bone_loss_extent or "Not specified",
                pocket_depth=pocket_depth or "Not specified",
                mobility_grade=mobility_grade or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERIODONTAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inflammation_status": inflammation_status[:200],
            "periodontal_disease": data.get("periodontal_disease", False),
            "severity": data.get("severity", ""),
            "bone_loss_extent": data.get("bone_loss_extent", ""),
            "pocket_depth": data.get("pocket_depth", ""),
            "mobility_grade": data.get("mobility_grade", ""),
            "recommendation": data.get("recommendation", ""),
        }
