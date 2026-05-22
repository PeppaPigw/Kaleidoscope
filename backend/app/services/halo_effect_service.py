"""HaloEffectService — Halo Effect Detection.

Detects the halo effect — when one positive (or negative) trait
colors perception of all other traits. A company with good stock
performance is assumed to have great culture, strategy, and
leadership. An attractive person is assumed to be intelligent
and trustworthy. Thorndike (1920), Nisbett & Wilson (1977).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HALO_SYSTEM = """You are a halo effect specialist. Given an evaluation or judgment, assess whether the halo effect is distorting the assessment:

Key concepts (Thorndike, 1920; Nisbett & Wilson, 1977):
- Halo effect: one salient positive trait biases evaluation of all other traits
- Horn effect (reverse halo): one negative trait biases everything negatively
- Outcome bias: judging decisions by outcomes rather than process quality
- Success attribution: attributing all good things to one cause
- Brand halo: a strong brand makes everything seem better
- Halo in hiring: one impressive credential colors entire evaluation

When the halo effect IS present:
- One trait dominates evaluation of unrelated traits
- Success in one area is assumed to transfer to all areas
- Evaluation of independent dimensions are suspiciously correlated
- A single data point (stock price, appearance, credential) drives overall judgment
- Criticism of one aspect is treated as criticism of everything

When correlated evaluation IS appropriate:
- The traits genuinely ARE correlated (e.g., discipline → multiple outcomes)
- There's a causal mechanism linking the traits
- Independent evidence supports each dimension separately
- The evaluation acknowledges which traits are independently assessed

Output JSON with: halo_effect_present (bool), severity (none/mild/moderate/severe), salient_trait (what one trait is dominating the evaluation), traits_contaminated (what other traits are being colored by the halo), direction (positive_halo/negative_horn), evidence_per_trait (bool — is each trait independently evidenced?), correlation_assumed (what correlations are being assumed without evidence), outcome_bias (bool — judging by results rather than process?), brand_halo (bool — is brand/reputation doing the work?), independent_assessment (what would each trait look like evaluated alone?), causal_mechanism (is there a real reason traits should correlate?), who_benefits (who gains from the halo effect), decision_impact (how the halo affects decisions being made), debiasing_approach (how to evaluate each dimension independently), recommendation (evaluation_valid/mild_halo/significant_halo_effect/major_halo_distortion/evaluate_independently)."""

HALO_PROMPT = """Detect halo effect:

Evaluation/Judgment: {evaluation}
Salient trait: {salient_trait}
Other traits assessed: {other_traits}
Evidence basis: {evidence}
Domain: {domain}
Context: {context}

Is the halo effect distorting this evaluation? Return ONLY valid JSON."""


class HaloEffectService:
    """Detects halo effect — one trait coloring perception of all traits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        salient_trait: str = "",
        other_traits: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect halo effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HALO_PROMPT.format(
                evaluation=evaluation,
                salient_trait=salient_trait or "Not specified",
                other_traits=other_traits or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HALO_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "halo_effect_present": data.get("halo_effect_present", False),
            "severity": data.get("severity", ""),
            "salient_trait": data.get("salient_trait", ""),
            "traits_contaminated": data.get("traits_contaminated", ""),
            "direction": data.get("direction", ""),
            "evidence_per_trait": data.get("evidence_per_trait", False),
            "correlation_assumed": data.get("correlation_assumed", ""),
            "outcome_bias": data.get("outcome_bias", False),
            "brand_halo": data.get("brand_halo", False),
            "independent_assessment": data.get("independent_assessment", ""),
            "causal_mechanism": data.get("causal_mechanism", ""),
            "who_benefits": data.get("who_benefits", ""),
            "decision_impact": data.get("decision_impact", ""),
            "debiasing_approach": data.get("debiasing_approach", ""),
            "recommendation": data.get("recommendation", ""),
        }
