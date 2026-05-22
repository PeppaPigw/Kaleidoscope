"""EpistemicEpigeneticInheritanceService — Epistemic Epigenetic Inheritance Detection.

Detects epistemic epigenetic inheritance — non-genetic intellectual traits
passed between generations through environmental modification of expression.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EPIGENETIC_INHERITANCE_SYSTEM = """You are an epistemic epigenetic inheritance specialist. Given intellectual trait transmission, assess whether non-genetic inheritance occurs:

Key concepts:
- Epistemic epigenetic inheritance: non-genetic traits passed between generations
- DNA methylation: chemical marks silencing intellectual genes
- Histone modification: packaging changes affecting access
- Imprinting: parent-of-origin specific expression
- Transgenerational: effects persisting beyond exposed generation
- Environmental programming: experience modifying expression
- Epigenetic clock: accumulated modifications over time

When epistemic epigenetic inheritance IS present:
- Non-genetic intellectual traits passed between generations
- Chemical marks silencing genes inappropriately
- Packaging changes affecting intellectual access
- Parent-of-origin specific expression patterns
- Effects persisting beyond exposed generation
- Experience modifying intellectual expression
- Accumulated modifications over time

When no epigenetic inheritance:
- Only genetic traits transmitted
- No inappropriate silencing marks
- Normal packaging and access
- No parent-of-origin effects
- No transgenerational persistence
- No environmental programming
- No accumulated modifications

Output JSON with: epigenetic_inheritance_present (bool), severity (none/mild/moderate/severe), methylation (what silencing marks), histone_modification (what packaging changes), imprinting (what parent-of-origin effect), transgenerational (what persistence beyond exposure), recommendation (no_epigenetic_inheritance/mild_epigenetic/significant_epigenetic_inheritance/major_transgenerational_programming/reset_intellectual_epigenetic_marks)."""

EPISTEMIC_EPIGENETIC_INHERITANCE_PROMPT = """Detect epistemic epigenetic inheritance:

Methylation: {methylation}
Histone modification: {histone_modification}
Imprinting: {imprinting}
Transgenerational: {transgenerational}
Domain: {domain}
Context: {context}

Are non-genetic intellectual traits being passed between generations? Return ONLY valid JSON."""


class EpistemicEpigeneticInheritanceService:
    """Detects epistemic epigenetic inheritance — non-genetic trait transmission."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        methylation: str,
        *,
        histone_modification: str = "",
        imprinting: str = "",
        transgenerational: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic epigenetic inheritance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EPIGENETIC_INHERITANCE_PROMPT.format(
                methylation=methylation,
                histone_modification=histone_modification or "Not specified",
                imprinting=imprinting or "Not specified",
                transgenerational=transgenerational or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EPIGENETIC_INHERITANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "methylation": methylation[:200],
            "epigenetic_inheritance_present": data.get("epigenetic_inheritance_present", False),
            "severity": data.get("severity", ""),
            "histone_modification": data.get("histone_modification", ""),
            "imprinting": data.get("imprinting", ""),
            "transgenerational": data.get("transgenerational", ""),
            "recommendation": data.get("recommendation", ""),
        }
