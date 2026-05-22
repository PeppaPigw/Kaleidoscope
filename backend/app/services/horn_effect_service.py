"""HornEffectService — Horn Effect Detection.

Detects horn effect — one negative trait or impression
contaminating overall judgment of unrelated attributes.
Inverse of halo effect. One bad quality creates "horns"
that color everything else negatively. A single mistake
makes someone seem incompetent at everything.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HORN_SYSTEM = """You are a horn effect specialist. Given an evaluation, assess whether one negative attribute is inappropriately contaminating judgment of unrelated attributes:

Key concepts (inverse of Thorndike's halo, 1920):
- Horn effect: one negative trait biases evaluation of unrelated traits negatively
- Devil effect: negative first impression colors all subsequent evaluation
- Negative trait generalization: one flaw → assumed flawed in all areas
- Physical unattractiveness bias: unattractive → assumed less competent
- Single failure contamination: one mistake → "they're bad at everything"
- Brand contamination: one bad product → all products assumed bad
- Guilt by association: negative connection → negative evaluation

When horn effect IS present:
- One mistake leading to overall negative evaluation
- Assuming someone bad at X must also be bad at Y (unrelated)
- A single negative trait overshadowing many positive ones
- "They failed at A, so they'll probably fail at B too"
- Physical appearance or one flaw contaminating professional evaluation
- Ignoring evidence of strength because of one weakness

When the negative evaluation IS justified:
- The negative trait is genuinely relevant to what's being evaluated
- There is direct evidence for each negative judgment
- The traits are genuinely correlated (carelessness → multiple domains)
- Multiple independent assessments confirm the negative evaluation
- The negative trait reveals a pattern, not an isolated incident

Output JSON with: horn_effect_present (bool), severity (none/mild/moderate/severe), subject (who/what is being evaluated), negative_trait (the trait creating the horn effect), contaminated_judgments (what unrelated judgments are affected), trait_relevance (is the negative trait relevant to the other judgments?), evidence_for_contaminated (what evidence exists for the negative judgments?), independent_assessment (would the negative judgments hold without the horn?), pattern_vs_incident (is this a pattern or isolated incident?), positive_traits_ignored (what strengths are being overlooked?), recommendation (evaluation_justified/mild_horn/significant_contamination/major_horn_distortion/evaluate_traits_independently)."""

HORN_PROMPT = """Detect horn effect:

Evaluation: {evaluation}
Negative trait: {negative_trait}
Other judgments: {other_judgments}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is one negative trait inappropriately contaminating unrelated judgments? Return ONLY valid JSON."""


class HornEffectService:
    """Detects horn effect — one negative trait contaminating overall evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        negative_trait: str = "",
        other_judgments: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect horn effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HORN_PROMPT.format(
                evaluation=evaluation,
                negative_trait=negative_trait or "Not specified",
                other_judgments=other_judgments or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HORN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "horn_effect_present": data.get("horn_effect_present", False),
            "severity": data.get("severity", ""),
            "negative_trait": data.get("negative_trait", ""),
            "contaminated_judgments": data.get("contaminated_judgments", ""),
            "trait_relevance": data.get("trait_relevance", ""),
            "evidence_for_contaminated": data.get("evidence_for_contaminated", ""),
            "independent_assessment": data.get("independent_assessment", ""),
            "pattern_vs_incident": data.get("pattern_vs_incident", ""),
            "positive_traits_ignored": data.get("positive_traits_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
