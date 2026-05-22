"""EpistemicMelanomaService — Epistemic Melanoma Detection.

Detects epistemic melanoma — malignant transformation of intellectual
pigment cells, where ideas meant to color thinking become cancerous growths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MELANOMA_SYSTEM = """You are an epistemic melanoma specialist. Given intellectual pigment changes, assess whether malignant transformation has occurred:

Key concepts:
- Epistemic melanoma: malignant transformation of intellectual pigment cells
- Asymmetry: irregular shape of intellectual growth
- Border irregularity: uneven edges of the idea
- Color variation: multiple shades within single concept
- Diameter growth: expanding beyond normal size
- Evolution: changing characteristics over time
- Metastasis: spreading to distant intellectual areas
- Sentinel node: first area of spread beyond origin

When epistemic melanoma IS present:
- Malignant transformation of coloring ideas
- Irregular asymmetric intellectual growth
- Uneven borders of the concept
- Multiple contradictory shades within single idea
- Expanding beyond normal conceptual size
- Changing characteristics over time
- Spreading to distant intellectual areas

When healthy pigmentation is present:
- Normal intellectual coloring
- Symmetric regular ideas
- Even clear borders
- Uniform consistent shade
- Stable appropriate size
- Unchanging characteristics
- Contained to appropriate area

Output JSON with: melanoma_present (bool), severity (none/mild/moderate/severe), asymmetry (what irregularity), border_irregularity (what uneven edges), color_variation (what multiple shades), evolution (what changes over time), recommendation (healthy_pigmentation/mild_atypia/significant_melanoma/major_malignant_transformation/excise_malignant_intellectual_growth)."""

EPISTEMIC_MELANOMA_PROMPT = """Detect epistemic melanoma:

Asymmetry: {asymmetry}
Border irregularity: {border_irregularity}
Color variation: {color_variation}
Evolution: {evolution}
Domain: {domain}
Context: {context}

Has malignant transformation occurred in intellectual pigment cells, with ideas meant to color thinking becoming cancerous? Return ONLY valid JSON."""


class EpistemicMelanomaService:
    """Detects epistemic melanoma — malignant transformation of intellectual pigment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        asymmetry: str,
        *,
        border_irregularity: str = "",
        color_variation: str = "",
        evolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic melanoma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MELANOMA_PROMPT.format(
                asymmetry=asymmetry,
                border_irregularity=border_irregularity or "Not specified",
                color_variation=color_variation or "Not specified",
                evolution=evolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MELANOMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "asymmetry": asymmetry[:200],
            "melanoma_present": data.get("melanoma_present", False),
            "severity": data.get("severity", ""),
            "border_irregularity": data.get("border_irregularity", ""),
            "color_variation": data.get("color_variation", ""),
            "evolution": data.get("evolution", ""),
            "recommendation": data.get("recommendation", ""),
        }
