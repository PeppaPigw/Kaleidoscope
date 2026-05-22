"""EcologicalFallacyService — Cross-Level Inference Error Detection.

Detects ecological fallacy (applying group stats to individuals) and
atomistic fallacy (generalizing individual observations to groups).
Identifies Simpson's paradox risks and level-of-analysis errors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ECOLOGICAL_SYSTEM = """You are a cross-level inference specialist. Given a claim, assess whether it commits an ecological fallacy or atomistic fallacy:
- Is a group-level finding being applied to individuals (ecological fallacy)?
- Is an individual observation being generalized to groups (atomistic fallacy)?
- Could Simpson's paradox reverse the finding at a different level?
- Is the level of analysis appropriate for the conclusion?
- What confounders operate differently at different levels?

Output JSON with: fallacy_present (bool), fallacy_type (ecological/atomistic/simpsons_paradox/none), severity (none/mild/moderate/severe), claim_level (individual/group/population/mixed), evidence_level (individual/group/population/mixed), level_mismatch (bool), simpsons_paradox_risk (0-1), confounders_across_levels (list of: confounder, how_it_differs_by_level), correct_level_conclusion (what we can conclude at the evidence level), incorrect_cross_level_conclusion (what's being wrongly inferred), example_of_reversal (scenario where the finding reverses at another level), proper_analysis (how to correctly test the cross-level claim), recommendation (valid/needs_individual_data/needs_group_data/cannot_cross_levels)."""

ECOLOGICAL_PROMPT = """Detect cross-level inference errors:

Claim: {claim}
Data level: {data_level}
Conclusion level: {conclusion_level}
Domain: {domain}
Context: {context}

Is there an ecological or atomistic fallacy? Return ONLY valid JSON."""


class EcologicalFallacyService:
    """Detects ecological fallacy and cross-level inference errors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        data_level: str = "",
        conclusion_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ecological fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ECOLOGICAL_PROMPT.format(
                claim=claim,
                data_level=data_level or "Not specified",
                conclusion_level=conclusion_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ECOLOGICAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "fallacy_present": data.get("fallacy_present", False),
            "fallacy_type": data.get("fallacy_type", ""),
            "severity": data.get("severity", ""),
            "claim_level": data.get("claim_level", ""),
            "evidence_level": data.get("evidence_level", ""),
            "level_mismatch": data.get("level_mismatch", False),
            "simpsons_paradox_risk": data.get("simpsons_paradox_risk", 0),
            "confounders_across_levels": data.get("confounders_across_levels", []),
            "correct_level_conclusion": data.get("correct_level_conclusion", ""),
            "incorrect_cross_level_conclusion": data.get("incorrect_cross_level_conclusion", ""),
            "example_of_reversal": data.get("example_of_reversal", ""),
            "proper_analysis": data.get("proper_analysis", ""),
            "recommendation": data.get("recommendation", ""),
        }
