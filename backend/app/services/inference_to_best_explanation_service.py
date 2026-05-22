"""InferenceToBestExplanationService — Inference to Best Explanation Assessment.

Evaluates whether the best available explanation has been
identified for a set of observations. Assesses whether alternative
explanations have been adequately considered and whether the
chosen explanation genuinely best accounts for the evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IBE_SYSTEM = """You are an inference to best explanation specialist. Given an explanatory claim, assess whether it genuinely represents the best available explanation:

Key concepts:
- Inference to best explanation (IBE): abductive reasoning
- Explanatory virtues: simplicity, scope, coherence, fertility
- Alternative explanations: what else could explain the evidence?
- Underdetermination: evidence consistent with multiple theories
- Occam's razor: prefer simpler explanations (all else equal)
- Ad hoc explanations: explanations created solely to fit the data
- Predictive power: does the explanation predict new observations?

Assessment criteria:
- Does the explanation account for all the evidence?
- Is it simpler than alternatives (Occam's razor)?
- Does it cohere with background knowledge?
- Does it make testable predictions?
- Have alternative explanations been considered?
- Is it ad hoc or does it have independent motivation?
- Does it have explanatory scope beyond the immediate data?

Output JSON with: ibe_quality (poor/fair/good/excellent), explanation (the proposed explanation), alternatives (other possible explanations), virtues (what makes this explanation good), weaknesses (where it falls short), best_alternative (the strongest competing explanation), recommendation (best_explanation_found/good_but_alternatives_exist/needs_more_alternatives/ad_hoc_explanation/better_alternative_available)."""

IBE_PROMPT = """Assess inference to best explanation:

Observations: {observations}
Proposed explanation: {explanation}
Alternatives considered: {alternatives}
Evidence fit: {evidence_fit}
Domain: {domain}
Context: {context}

Is this genuinely the best available explanation for the observations? Return ONLY valid JSON."""


class InferenceToBestExplanationService:
    """Assesses whether the best explanation has been identified."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        observations: str,
        *,
        explanation: str = "",
        alternatives: str = "",
        evidence_fit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess inference to best explanation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IBE_PROMPT.format(
                observations=observations,
                explanation=explanation or "Not specified",
                alternatives=alternatives or "Not specified",
                evidence_fit=evidence_fit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=IBE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "observations": observations[:200],
            "ibe_quality": data.get("ibe_quality", ""),
            "explanation": data.get("explanation", ""),
            "alternatives": data.get("alternatives", ""),
            "virtues": data.get("virtues", ""),
            "best_alternative": data.get("best_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
