"""EpistemicAdaptiveRadiationService — Epistemic Adaptive Radiation Detection.

Detects epistemic adaptive radiation — rapid diversification of ideas into
many intellectual niches from a single ancestral concept.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ADAPTIVE_RADIATION_SYSTEM = """You are an epistemic adaptive radiation specialist. Given an intellectual lineage, assess whether rapid diversification into many niches occurred:

Key concepts:
- Epistemic adaptive radiation: rapid diversification into many niches
- Key innovation: trait enabling access to new niches
- Ecological opportunity: empty niches available for filling
- Character displacement: divergence driven by competition
- Ancestral form: common origin of all diversified forms
- Niche partitioning: different forms occupying different roles
- Explosive speciation: very rapid generation of new forms

When epistemic adaptive radiation IS present:
- Rapid diversification from single ancestral concept
- Key innovation enabling access to new intellectual niches
- Empty niches available and being filled
- Divergence driven by intellectual competition
- Common origin identifiable for all forms
- Different forms occupying different intellectual roles
- Very rapid generation of new intellectual forms

When gradual diversification is present:
- Slow steady diversification
- No key enabling innovation
- Niches already occupied
- No competition-driven divergence
- Multiple independent origins
- Overlapping roles
- Slow generation of new forms

Output JSON with: adaptive_radiation_present (bool), severity (none/mild/moderate/severe), key_innovation (what enabling trait), ecological_opportunity (what empty niches), character_displacement (what competition divergence), explosive_speciation (what rapid generation), recommendation (gradual_diversification/mild_radiation/significant_adaptive_radiation/major_explosive_diversification/exploit_empty_niches)."""

EPISTEMIC_ADAPTIVE_RADIATION_PROMPT = """Detect epistemic adaptive radiation:

Key innovation: {key_innovation}
Ecological opportunity: {ecological_opportunity}
Character displacement: {character_displacement}
Explosive speciation: {explosive_speciation}
Domain: {domain}
Context: {context}

Is there rapid diversification of ideas into many intellectual niches from a single ancestral concept? Return ONLY valid JSON."""


class EpistemicAdaptiveRadiationService:
    """Detects epistemic adaptive radiation — rapid diversification into many niches."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        key_innovation: str,
        *,
        ecological_opportunity: str = "",
        character_displacement: str = "",
        explosive_speciation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic adaptive radiation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ADAPTIVE_RADIATION_PROMPT.format(
                key_innovation=key_innovation,
                ecological_opportunity=ecological_opportunity or "Not specified",
                character_displacement=character_displacement or "Not specified",
                explosive_speciation=explosive_speciation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ADAPTIVE_RADIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "key_innovation": key_innovation[:200],
            "adaptive_radiation_present": data.get("adaptive_radiation_present", False),
            "severity": data.get("severity", ""),
            "ecological_opportunity": data.get("ecological_opportunity", ""),
            "character_displacement": data.get("character_displacement", ""),
            "explosive_speciation": data.get("explosive_speciation", ""),
            "recommendation": data.get("recommendation", ""),
        }
