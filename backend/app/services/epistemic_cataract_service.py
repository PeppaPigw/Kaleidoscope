"""EpistemicCataractService — Epistemic Cataract Detection.

Detects epistemic cataract — clouding of the intellectual lens that
obscures clear vision and reduces contrast sensitivity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CATARACT_SYSTEM = """You are an epistemic cataract specialist. Given intellectual lens clarity, assess whether clouding obscures vision:

Key concepts:
- Epistemic cataract: clouding of intellectual lens obscuring vision
- Nuclear sclerosis: central lens hardening and yellowing
- Cortical opacity: peripheral clouding spreading inward
- Posterior subcapsular: clouding at back of lens affecting reading
- Contrast sensitivity loss: inability to distinguish subtle differences
- Glare sensitivity: bright ideas causing scatter and confusion
- Lens replacement: removing clouded lens for clear artificial one

When epistemic cataract IS present:
- Clouding of intellectual lens obscuring clear vision
- Central lens hardening and yellowing perception
- Peripheral clouding spreading inward
- Clouding affecting close intellectual work
- Inability to distinguish subtle differences
- Bright ideas causing scatter and confusion
- Need to replace clouded intellectual lens

When clear lens is present:
- Transparent intellectual lens
- No central hardening
- No peripheral clouding
- Clear close work
- Full contrast sensitivity
- No glare problems
- No replacement needed

Output JSON with: cataract_present (bool), severity (none/mild/moderate/severe), nuclear_sclerosis (what central clouding), cortical_opacity (what peripheral clouding), contrast_loss (what distinction inability), glare_sensitivity (what scatter confusion), recommendation (clear_lens/mild_cataract/significant_cataract/major_lens_clouding/replace_intellectual_lens)."""

EPISTEMIC_CATARACT_PROMPT = """Detect epistemic cataract:

Nuclear sclerosis: {nuclear_sclerosis}
Cortical opacity: {cortical_opacity}
Contrast loss: {contrast_loss}
Glare sensitivity: {glare_sensitivity}
Domain: {domain}
Context: {context}

Is clouding of the intellectual lens obscuring clear vision? Return ONLY valid JSON."""


class EpistemicCataractService:
    """Detects epistemic cataract — clouding of intellectual lens."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        nuclear_sclerosis: str,
        *,
        cortical_opacity: str = "",
        contrast_loss: str = "",
        glare_sensitivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cataract."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CATARACT_PROMPT.format(
                nuclear_sclerosis=nuclear_sclerosis,
                cortical_opacity=cortical_opacity or "Not specified",
                contrast_loss=contrast_loss or "Not specified",
                glare_sensitivity=glare_sensitivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CATARACT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "nuclear_sclerosis": nuclear_sclerosis[:200],
            "cataract_present": data.get("cataract_present", False),
            "severity": data.get("severity", ""),
            "cortical_opacity": data.get("cortical_opacity", ""),
            "contrast_loss": data.get("contrast_loss", ""),
            "glare_sensitivity": data.get("glare_sensitivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
