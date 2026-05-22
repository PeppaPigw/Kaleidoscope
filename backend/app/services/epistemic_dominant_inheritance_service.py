"""EpistemicDominantInheritanceService — Epistemic Dominant Inheritance Detection.

Detects epistemic dominant inheritance — single intellectual gene overpowering
all alternatives, where one idea dominates regardless of context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOMINANT_INHERITANCE_SYSTEM = """You are an epistemic dominant inheritance specialist. Given intellectual lineage patterns, assess whether single genes overpower alternatives:

Key concepts:
- Epistemic dominant inheritance: single intellectual gene overpowering alternatives
- Penetrance: how often the dominant trait manifests
- Expressivity: how strongly the trait presents
- De novo mutation: new dominant appearing without family history
- Haploinsufficiency: one copy insufficient for normal function
- Dominant negative: mutant product interfering with normal
- Anticipation: trait worsening across generations

When epistemic dominant inheritance IS present:
- Single intellectual gene overpowering all alternatives
- High penetrance of dominant trait
- Strong expression of the trait
- New dominants appearing without history
- One copy insufficient for balance
- Mutant ideas interfering with normal ones
- Trait worsening across intellectual generations

When balanced inheritance is present:
- No single gene dominance
- Balanced trait expression
- Moderate expressivity
- Stable family history
- Both copies contributing
- No interference between ideas
- Stable across generations

Output JSON with: dominant_inheritance_present (bool), severity (none/mild/moderate/severe), penetrance (what manifestation frequency), expressivity (what strength), de_novo (what new appearance), dominant_negative (what interference), recommendation (balanced_inheritance/mild_dominance/significant_dominant_inheritance/major_single_gene_tyranny/restore_intellectual_allelic_balance)."""

EPISTEMIC_DOMINANT_INHERITANCE_PROMPT = """Detect epistemic dominant inheritance:

Penetrance: {penetrance}
Expressivity: {expressivity}
De novo: {de_novo}
Dominant negative: {dominant_negative}
Domain: {domain}
Context: {context}

Is a single intellectual gene overpowering all alternatives? Return ONLY valid JSON."""


class EpistemicDominantInheritanceService:
    """Detects epistemic dominant inheritance — single gene overpowering alternatives."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        penetrance: str,
        *,
        expressivity: str = "",
        de_novo: str = "",
        dominant_negative: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dominant inheritance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOMINANT_INHERITANCE_PROMPT.format(
                penetrance=penetrance,
                expressivity=expressivity or "Not specified",
                de_novo=de_novo or "Not specified",
                dominant_negative=dominant_negative or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOMINANT_INHERITANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "penetrance": penetrance[:200],
            "dominant_inheritance_present": data.get("dominant_inheritance_present", False),
            "severity": data.get("severity", ""),
            "expressivity": data.get("expressivity", ""),
            "de_novo": data.get("de_novo", ""),
            "dominant_negative": data.get("dominant_negative", ""),
            "recommendation": data.get("recommendation", ""),
        }
