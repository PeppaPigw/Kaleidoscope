"""EpistemicGeneticBottleneckService — Epistemic Genetic Bottleneck Detection.

Detects epistemic genetic bottleneck — intellectual diversity drastically
reduced by a catastrophic event, leaving only a narrow surviving lineage.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GENETIC_BOTTLENECK_SYSTEM = """You are an epistemic genetic bottleneck specialist. Given an intellectual population, assess whether diversity was drastically reduced:

Key concepts:
- Epistemic genetic bottleneck: diversity drastically reduced by catastrophe
- Founder effect: small surviving group determining future diversity
- Genetic drift: random changes amplified in small populations
- Heterozygosity loss: reduction in variation
- Recovery time: how long to rebuild diversity
- Selective sweep: single variant eliminating all others
- Population crash: sudden reduction in intellectual variety

When epistemic genetic bottleneck IS present:
- Intellectual diversity drastically reduced by an event
- Small surviving group determining all future development
- Random effects amplified due to small population
- Measurable reduction in intellectual variation
- Long recovery time needed to rebuild diversity
- Single variant having eliminated all alternatives
- Sudden crash in intellectual variety

When diverse population is present:
- Full intellectual diversity maintained
- Large population with many lineages
- Random effects averaged out
- High variation maintained
- No recovery needed
- Multiple variants coexisting
- Stable population size

Output JSON with: genetic_bottleneck_present (bool), severity (none/mild/moderate/severe), founder_effect (what surviving group), genetic_drift (what random amplification), heterozygosity_loss (what variation reduction), recovery_time (what rebuilding needed), recommendation (diverse_population/mild_bottleneck/significant_genetic_bottleneck/major_diversity_loss/actively_rebuild_diversity)."""

EPISTEMIC_GENETIC_BOTTLENECK_PROMPT = """Detect epistemic genetic bottleneck:

Founder effect: {founder_effect}
Genetic drift: {genetic_drift}
Heterozygosity loss: {heterozygosity_loss}
Recovery time: {recovery_time}
Domain: {domain}
Context: {context}

Was intellectual diversity drastically reduced by a catastrophic event, leaving only a narrow surviving lineage? Return ONLY valid JSON."""


class EpistemicGeneticBottleneckService:
    """Detects epistemic genetic bottleneck — diversity drastically reduced."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        founder_effect: str,
        *,
        genetic_drift: str = "",
        heterozygosity_loss: str = "",
        recovery_time: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic genetic bottleneck."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GENETIC_BOTTLENECK_PROMPT.format(
                founder_effect=founder_effect,
                genetic_drift=genetic_drift or "Not specified",
                heterozygosity_loss=heterozygosity_loss or "Not specified",
                recovery_time=recovery_time or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GENETIC_BOTTLENECK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "founder_effect": founder_effect[:200],
            "genetic_bottleneck_present": data.get("genetic_bottleneck_present", False),
            "severity": data.get("severity", ""),
            "genetic_drift": data.get("genetic_drift", ""),
            "heterozygosity_loss": data.get("heterozygosity_loss", ""),
            "recovery_time": data.get("recovery_time", ""),
            "recommendation": data.get("recommendation", ""),
        }
