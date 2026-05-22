"""EpistemicIntestinalFloraService — Epistemic Intestinal Flora Detection.

Detects epistemic intestinal flora — symbiotic intellectual organisms
that aid in the digestion and processing of complex ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTESTINAL_FLORA_SYSTEM = """You are an epistemic intestinal flora specialist. Given an intellectual ecosystem, assess whether symbiotic organisms aid digestion:

Key concepts:
- Epistemic intestinal flora: symbiotic organisms aiding idea digestion
- Microbiome diversity: variety of helpful intellectual organisms
- Dysbiosis: imbalance in the intellectual ecosystem
- Probiotic: beneficial organism introduced to restore balance
- Prebiotic: substrate that feeds beneficial organisms
- Colonization resistance: healthy flora preventing pathogen establishment
- Metabolite production: useful byproducts from flora activity

When epistemic intestinal flora IS present:
- Symbiotic organisms aiding idea digestion
- Diverse helpful intellectual organisms
- Potential imbalance in the ecosystem
- Beneficial organisms introduced for balance
- Substrates feeding beneficial processes
- Healthy flora preventing harmful establishment
- Useful byproducts from symbiotic activity

When no flora is present:
- No symbiotic organisms
- No microbiome diversity
- No dysbiosis possible
- No probiotics needed
- No prebiotics relevant
- No colonization resistance
- No metabolite production

Output JSON with: intestinal_flora_present (bool), severity (none/mild/moderate/severe), microbiome_diversity (what variety), dysbiosis (what imbalance), colonization_resistance (what pathogen prevention), metabolite_production (what useful byproducts), recommendation (no_flora/mild_flora/significant_intestinal_flora/major_symbiotic_ecosystem/optimize_flora_balance)."""

EPISTEMIC_INTESTINAL_FLORA_PROMPT = """Detect epistemic intestinal flora:

Microbiome diversity: {microbiome_diversity}
Dysbiosis: {dysbiosis}
Colonization resistance: {colonization_resistance}
Metabolite production: {metabolite_production}
Domain: {domain}
Context: {context}

Are symbiotic intellectual organisms aiding in the digestion of complex ideas? Return ONLY valid JSON."""


class EpistemicIntestinalFloraService:
    """Detects epistemic intestinal flora — symbiotic organisms aiding digestion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        microbiome_diversity: str,
        *,
        dysbiosis: str = "",
        colonization_resistance: str = "",
        metabolite_production: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intestinal flora."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTESTINAL_FLORA_PROMPT.format(
                microbiome_diversity=microbiome_diversity,
                dysbiosis=dysbiosis or "Not specified",
                colonization_resistance=colonization_resistance or "Not specified",
                metabolite_production=metabolite_production or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTESTINAL_FLORA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "microbiome_diversity": microbiome_diversity[:200],
            "intestinal_flora_present": data.get("intestinal_flora_present", False),
            "severity": data.get("severity", ""),
            "dysbiosis": data.get("dysbiosis", ""),
            "colonization_resistance": data.get("colonization_resistance", ""),
            "metabolite_production": data.get("metabolite_production", ""),
            "recommendation": data.get("recommendation", ""),
        }
