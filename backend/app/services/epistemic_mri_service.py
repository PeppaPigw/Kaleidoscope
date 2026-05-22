"""EpistemicMriService — Epistemic MRI Detection.

Detects need for epistemic MRI — deep structural imaging revealing hidden
intellectual lesions invisible to surface examination.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MRI_SYSTEM = """You are an epistemic MRI specialist. Given intellectual structures, assess whether deep hidden lesions exist:

Key concepts:
- Epistemic MRI: deep structural imaging of intellectual tissue
- White matter lesion: damage to connecting pathways
- Mass effect: lesion pushing surrounding structures
- Enhancement: lesion actively growing or inflamed
- Diffusion restriction: acute damage pattern
- Atrophy: loss of intellectual volume
- Signal abnormality: tissue behaving differently from normal

When epistemic MRI findings ARE present:
- Hidden lesions invisible to surface examination
- Damage to connecting intellectual pathways
- Lesions pushing surrounding structures aside
- Active growth or inflammation of lesions
- Acute damage patterns in intellectual tissue
- Loss of intellectual volume
- Tissue behaving abnormally

When healthy structure is present:
- No hidden lesions
- Intact connecting pathways
- No mass effect
- No active growth
- No acute damage
- Normal intellectual volume
- Normal tissue behavior

Output JSON with: mri_findings_present (bool), severity (none/mild/moderate/severe), white_matter_lesion (what pathway damage), mass_effect (what displacement), enhancement (what active growth), atrophy (what volume loss), recommendation (healthy_structure/mild_findings/significant_lesions/major_structural_disease/intervene_deep_intellectual_pathology)."""

EPISTEMIC_MRI_PROMPT = """Detect epistemic MRI findings:

White matter lesion: {white_matter_lesion}
Mass effect: {mass_effect}
Enhancement: {enhancement}
Atrophy: {atrophy}
Domain: {domain}
Context: {context}

Are there deep hidden intellectual lesions invisible to surface examination? Return ONLY valid JSON."""


class EpistemicMriService:
    """Detects epistemic MRI findings — deep hidden intellectual lesions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        white_matter_lesion: str,
        *,
        mass_effect: str = "",
        enhancement: str = "",
        atrophy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic MRI findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MRI_PROMPT.format(
                white_matter_lesion=white_matter_lesion,
                mass_effect=mass_effect or "Not specified",
                enhancement=enhancement or "Not specified",
                atrophy=atrophy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MRI_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "white_matter_lesion": white_matter_lesion[:200],
            "mri_findings_present": data.get("mri_findings_present", False),
            "severity": data.get("severity", ""),
            "mass_effect": data.get("mass_effect", ""),
            "enhancement": data.get("enhancement", ""),
            "atrophy": data.get("atrophy", ""),
            "recommendation": data.get("recommendation", ""),
        }
