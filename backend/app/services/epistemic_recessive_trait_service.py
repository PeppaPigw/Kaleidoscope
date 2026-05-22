"""EpistemicRecessiveTraitService — Epistemic Recessive Trait Detection.

Detects epistemic recessive traits — hidden intellectual traits that emerge
only when homozygous, invisible in carriers but powerful when expressed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RECESSIVE_TRAIT_SYSTEM = """You are an epistemic recessive trait specialist. Given intellectual lineage, assess whether hidden traits emerge when homozygous:

Key concepts:
- Epistemic recessive trait: hidden intellectual trait emerging when homozygous
- Carrier state: possessing trait without expressing it
- Consanguinity: intellectual inbreeding increasing homozygosity
- Founder effect: rare trait concentrated in isolated population
- Complementation: two different recessive mutations canceling each other
- Heterozygote advantage: carriers having benefit over non-carriers
- Genetic counseling: predicting recessive trait emergence

When epistemic recessive trait IS present:
- Hidden intellectual traits emerging when homozygous
- Carrier state masking the trait
- Intellectual inbreeding increasing expression
- Rare traits concentrated in isolated groups
- Different mutations potentially canceling each other
- Carriers having unexpected advantages
- Predictable emergence patterns

When no recessive traits:
- All traits visibly expressed
- No carrier states
- No inbreeding effects
- No founder effects
- No complementation needed
- No heterozygote advantage
- No hidden trait prediction needed

Output JSON with: recessive_trait_present (bool), severity (none/mild/moderate/severe), carrier_state (what hidden possession), consanguinity (what inbreeding), founder_effect (what concentration), heterozygote_advantage (what carrier benefit), recommendation (no_recessive_traits/mild_carrier_state/significant_recessive_expression/major_homozygous_emergence/diversify_intellectual_gene_pool)."""

EPISTEMIC_RECESSIVE_TRAIT_PROMPT = """Detect epistemic recessive trait:

Carrier state: {carrier_state}
Consanguinity: {consanguinity}
Founder effect: {founder_effect}
Heterozygote advantage: {heterozygote_advantage}
Domain: {domain}
Context: {context}

Are hidden intellectual traits emerging only when homozygous? Return ONLY valid JSON."""


class EpistemicRecessiveTraitService:
    """Detects epistemic recessive traits — hidden traits emerging when homozygous."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        carrier_state: str,
        *,
        consanguinity: str = "",
        founder_effect: str = "",
        heterozygote_advantage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic recessive trait."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RECESSIVE_TRAIT_PROMPT.format(
                carrier_state=carrier_state,
                consanguinity=consanguinity or "Not specified",
                founder_effect=founder_effect or "Not specified",
                heterozygote_advantage=heterozygote_advantage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RECESSIVE_TRAIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "carrier_state": carrier_state[:200],
            "recessive_trait_present": data.get("recessive_trait_present", False),
            "severity": data.get("severity", ""),
            "consanguinity": data.get("consanguinity", ""),
            "founder_effect": data.get("founder_effect", ""),
            "heterozygote_advantage": data.get("heterozygote_advantage", ""),
            "recommendation": data.get("recommendation", ""),
        }
