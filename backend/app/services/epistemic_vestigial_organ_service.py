"""EpistemicVestigialOrganService — Epistemic Vestigial Organ Detection.

Detects epistemic vestigial organ — intellectual structures that once served
a purpose but are now functionless, persisting as historical remnants.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VESTIGIAL_ORGAN_SYSTEM = """You are an epistemic vestigial organ specialist. Given an intellectual structure, assess whether it once served a purpose but is now functionless:

Key concepts:
- Epistemic vestigial organ: structure persisting without current function
- Atavism: ancestral trait reappearing
- Degeneration: gradual loss of function over time
- Historical constraint: structure persisting due to developmental path
- Exaptation: repurposing for new function
- Phylogenetic inertia: resistance to losing old structures
- Neutral evolution: structure drifting without selection

When epistemic vestigial organ IS present:
- Intellectual structures persisting without current function
- Ancestral intellectual traits occasionally reappearing
- Gradual loss of original function over time
- Structure persisting due to historical path
- Possible repurposing for new function
- Resistance to removing old intellectual structures
- Structure drifting without selective pressure

When functional structure is present:
- All structures serving current function
- No ancestral reappearances
- Functions maintained over time
- Structure present due to current utility
- No repurposing needed
- Easy removal of unused structures
- Active selection maintaining structure

Output JSON with: vestigial_organ_present (bool), severity (none/mild/moderate/severe), atavism (what ancestral reappearance), degeneration (what function loss), historical_constraint (what path dependence), exaptation (what repurposing potential), recommendation (functional_structure/mild_vestigial/significant_vestigial_organ/major_functionless_remnant/repurpose_or_remove)."""

EPISTEMIC_VESTIGIAL_ORGAN_PROMPT = """Detect epistemic vestigial organ:

Atavism: {atavism}
Degeneration: {degeneration}
Historical constraint: {historical_constraint}
Exaptation: {exaptation}
Domain: {domain}
Context: {context}

Are intellectual structures persisting that once served a purpose but are now functionless historical remnants? Return ONLY valid JSON."""


class EpistemicVestigialOrganService:
    """Detects epistemic vestigial organ — functionless historical remnants."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        atavism: str,
        *,
        degeneration: str = "",
        historical_constraint: str = "",
        exaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vestigial organ."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VESTIGIAL_ORGAN_PROMPT.format(
                atavism=atavism,
                degeneration=degeneration or "Not specified",
                historical_constraint=historical_constraint or "Not specified",
                exaptation=exaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VESTIGIAL_ORGAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "atavism": atavism[:200],
            "vestigial_organ_present": data.get("vestigial_organ_present", False),
            "severity": data.get("severity", ""),
            "degeneration": data.get("degeneration", ""),
            "historical_constraint": data.get("historical_constraint", ""),
            "exaptation": data.get("exaptation", ""),
            "recommendation": data.get("recommendation", ""),
        }
