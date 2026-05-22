"""EpistemicBioaccumulationService — Epistemic Bioaccumulation Detection.

Detects epistemic bioaccumulation — toxic ideas concentrating up the
intellectual food chain, becoming more dangerous at higher levels.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BIOACCUMULATION_SYSTEM = """You are an epistemic bioaccumulation specialist. Given intellectual food chain dynamics, assess whether toxic concentration is increasing at higher levels:

Key concepts:
- Epistemic bioaccumulation: toxic ideas concentrating up the chain
- Biomagnification: increasing concentration at each trophic level
- Persistent toxin: ideas that resist intellectual breakdown
- Trophic transfer: toxin passing from lower to higher level
- Apex predator burden: highest-level thinkers most contaminated
- Half-life: time for toxin concentration to halve
- Bioconcentration factor: ratio of internal to external concentration

When epistemic bioaccumulation IS present:
- Toxic ideas concentrating up the intellectual chain
- Increasing concentration at each level of abstraction
- Ideas resisting intellectual breakdown
- Toxin passing from basic to advanced thinking
- Highest-level thinkers most contaminated
- Long half-life of toxic ideas
- High internal-to-external concentration ratio

When healthy ecosystem is present:
- No toxic concentration
- Stable levels across chain
- Ideas properly metabolized
- Clean transfer between levels
- Apex thinkers uncontaminated
- Short half-life of harmful ideas
- Low concentration ratio

Output JSON with: bioaccumulation_present (bool), severity (none/mild/moderate/severe), biomagnification (what increasing concentration), persistent_toxin (what resists breakdown), apex_burden (what highest-level contamination), half_life (what persistence), recommendation (healthy_ecosystem/mild_bioaccumulation/significant_bioaccumulation/major_toxic_concentration/decontaminate_intellectual_food_chain)."""

EPISTEMIC_BIOACCUMULATION_PROMPT = """Detect epistemic bioaccumulation:

Biomagnification: {biomagnification}
Persistent toxin: {persistent_toxin}
Apex burden: {apex_burden}
Half life: {half_life}
Domain: {domain}
Context: {context}

Are toxic ideas concentrating up the intellectual food chain? Return ONLY valid JSON."""


class EpistemicBioaccumulationService:
    """Detects epistemic bioaccumulation — toxic concentration up intellectual chain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        biomagnification: str,
        *,
        persistent_toxin: str = "",
        apex_burden: str = "",
        half_life: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bioaccumulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BIOACCUMULATION_PROMPT.format(
                biomagnification=biomagnification,
                persistent_toxin=persistent_toxin or "Not specified",
                apex_burden=apex_burden or "Not specified",
                half_life=half_life or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BIOACCUMULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "biomagnification": biomagnification[:200],
            "bioaccumulation_present": data.get("bioaccumulation_present", False),
            "severity": data.get("severity", ""),
            "persistent_toxin": data.get("persistent_toxin", ""),
            "apex_burden": data.get("apex_burden", ""),
            "half_life": data.get("half_life", ""),
            "recommendation": data.get("recommendation", ""),
        }
