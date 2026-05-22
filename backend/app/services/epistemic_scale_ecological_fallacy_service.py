"""EpistemicScaleEcologicalFallacyService - Epistemic Scale Ecological Fallacy Detection.

Detects ecological fallacy inferring individual properties from group data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCALE_ECOLOGICAL_FALLACY_SYSTEM = """You are an epistemic scale ecological fallacy specialist. Given group-to-individual inference, assess ecological fallacy:

Key concepts:
- Epistemic scale ecological fallacy: inferring individual properties from group data
- Group-to-individual inference: applying aggregate facts to individuals
- Aggregate misapplication: using group statistics as individual claims
- Distribution ignorance: ignoring variance within the group
- Heterogeneity blindness: treating the group as uniform

When ecological fallacy IS present:
- Group data is applied to individuals
- Aggregate statistics are misused
- Distributions are ignored
- Heterogeneity is missed
- Individual variation is erased

When no ecological fallacy:
- Group and individual levels are distinguished
- Aggregate statistics are bounded
- Distributions are considered
- Heterogeneity is acknowledged
- Individual evidence is required for individual claims

Output JSON with: ecological_fallacy_detected (bool), severity (none/mild/moderate/severe), aggregate_misapplication (what aggregate data is misapplied), distribution_ignorance (what distribution is ignored), heterogeneity_blindness (what heterogeneity is missed), recommendation (no_ecological_fallacy/mild_distribution_check/significant_disaggregation/major_individual_level_analysis/emergency_complete_ecological_fallacy)."""

EPISTEMIC_SCALE_ECOLOGICAL_FALLACY_PROMPT = """Detect epistemic scale ecological fallacy:

Group-to-individual inference: {group_to_individual_inference}
Aggregate misapplication: {aggregate_misapplication}
Distribution ignorance: {distribution_ignorance}
Heterogeneity blindness: {heterogeneity_blindness}
Domain: {domain}
Context: {context}

Are individual properties being inferred from group data? Return ONLY valid JSON."""


class EpistemicScaleEcologicalFallacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        group_to_individual_inference: str,
        *,
        aggregate_misapplication: str = "",
        distribution_ignorance: str = "",
        heterogeneity_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCALE_ECOLOGICAL_FALLACY_PROMPT.format(
                group_to_individual_inference=group_to_individual_inference,
                aggregate_misapplication=aggregate_misapplication or "Not specified",
                distribution_ignorance=distribution_ignorance or "Not specified",
                heterogeneity_blindness=heterogeneity_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCALE_ECOLOGICAL_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "group_to_individual_inference": group_to_individual_inference[:200],
            "ecological_fallacy_detected": data.get("ecological_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "aggregate_misapplication": data.get("aggregate_misapplication", ""),
            "distribution_ignorance": data.get("distribution_ignorance", ""),
            "heterogeneity_blindness": data.get("heterogeneity_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
