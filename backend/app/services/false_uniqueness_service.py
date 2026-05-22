"""FalseUniquenessService — False Uniqueness Effect Detection.

Detects the false uniqueness effect — underestimating how common
your abilities, positive traits, or desirable behaviors are.
Suls & Wan (1987). The flip side of false consensus: you think
your good qualities are rarer than they are, inflating your
sense of specialness. "I'm one of the few who..."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_UNIQUENESS_SYSTEM = """You are a false uniqueness effect specialist. Given a self-assessment, determine whether the person is underestimating how common their traits or behaviors are:

Key concepts (Suls & Wan, 1987):
- False uniqueness: underestimating how common your positive traits/abilities are
- Self-enhancement motive: feeling special by believing your qualities are rare
- Above-average effect overlap: but false uniqueness is about rarity, not superiority
- Asymmetry with false consensus: we overestimate agreement for opinions but underestimate commonality of abilities
- Better-than-average illusion: most people think they're above average
- Illusory superiority: overestimating one's qualities relative to others

When false uniqueness IS present:
- "I'm one of the few people who..." (for common traits)
- Believing your work ethic, intelligence, or morality is rare
- Underestimating how many others share your positive behaviors
- Feeling uniquely virtuous, skilled, or insightful
- Surprise when others demonstrate the same ability
- Using rarity of trait as part of identity

When uniqueness IS real:
- Objective data shows the trait/behavior is genuinely rare
- The skill level is demonstrably exceptional (top percentile)
- The combination of traits is unusual even if individual traits aren't
- External validation confirms rarity (awards, selection, metrics)

Output JSON with: false_uniqueness_present (bool), severity (none/mild/moderate/severe), claimed_trait (what trait is believed to be unique), actual_prevalence (how common the trait actually is), prevalence_gap (difference between believed and actual rarity), self_enhancement_motive (bool — is this serving ego?), identity_investment (how tied to identity is the uniqueness claim?), evidence_for_rarity (what supports the uniqueness claim), evidence_against_rarity (what suggests it's common), comparison_group (who is the person comparing against?), objective_data (any data on actual prevalence?), consequences (what happens from this belief?), recommendation (uniqueness_warranted/mild_overestimation/significant_false_uniqueness/major_false_uniqueness/trait_is_common)."""

FALSE_UNIQUENESS_PROMPT = """Detect false uniqueness effect:

Self-assessment: {assessment}
Claimed unique trait: {trait}
Comparison group: {comparison}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is the person underestimating how common their traits are? Return ONLY valid JSON."""


class FalseUniquenessService:
    """Detects false uniqueness effect — underestimating commonality of positive traits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        trait: str = "",
        comparison: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false uniqueness effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_UNIQUENESS_PROMPT.format(
                assessment=assessment,
                trait=trait or "Not specified",
                comparison=comparison or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_UNIQUENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "false_uniqueness_present": data.get("false_uniqueness_present", False),
            "severity": data.get("severity", ""),
            "claimed_trait": data.get("claimed_trait", ""),
            "actual_prevalence": data.get("actual_prevalence", ""),
            "prevalence_gap": data.get("prevalence_gap", ""),
            "self_enhancement_motive": data.get("self_enhancement_motive", False),
            "identity_investment": data.get("identity_investment", ""),
            "evidence_for_rarity": data.get("evidence_for_rarity", ""),
            "evidence_against_rarity": data.get("evidence_against_rarity", ""),
            "comparison_group": data.get("comparison_group", ""),
            "objective_data": data.get("objective_data", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
