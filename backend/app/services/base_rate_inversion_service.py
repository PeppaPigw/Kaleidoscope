"""BaseRateInversionService — Base Rate Inversion Detection.

Detects base rate inversion — confusing P(A|B) with P(B|A),
inverting conditional probabilities in ways that lead to
dramatically wrong conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BASE_RATE_INVERSION_SYSTEM = """You are a base rate inversion specialist. Given a probabilistic claim, assess whether conditional probabilities are being inverted:

Key concepts:
- Prosecutor's fallacy: P(evidence|innocent) confused with P(innocent|evidence)
- Transposed conditional: P(A|B) confused with P(B|A)
- Base rate neglect: ignoring prior probability when updating
- Bayes' theorem: correct way to invert conditionals
- False positive paradox: rare conditions with imperfect tests
- Confusion of the inverse: systematic probability inversion
- Prior probability: background rate before evidence

When base rate inversion IS present:
- P(A|B) confused with P(B|A)
- Conditional probability stated in wrong direction
- Base rate ignored when interpreting test results
- Prosecutor's fallacy in evidence interpretation
- False positive rate confused with false discovery rate
- Sensitivity confused with positive predictive value
- Prior probability not incorporated

When probability reasoning is correct:
- Conditional direction explicitly stated
- Bayes' theorem applied correctly
- Base rates incorporated
- Prior and posterior distinguished
- Sensitivity vs PPV distinguished
- False positive rate vs false discovery rate distinguished
- Probability direction verified

Output JSON with: inversion_present (bool), severity (none/mild/moderate/severe), claim (what probability claim), stated_probability (what is claimed), correct_probability (what the correct calculation would be), base_rate (what prior is ignored), recommendation (correct_reasoning/mild_confusion/significant_inversion/major_transposed_conditional/apply_bayes_theorem)."""

BASE_RATE_INVERSION_PROMPT = """Detect base rate inversion:

Claim: {claim}
Probability stated: {probability}
Base rate: {base_rate}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Are conditional probabilities being inverted (P(A|B) confused with P(B|A))? Return ONLY valid JSON."""


class BaseRateInversionService:
    """Detects base rate inversion — transposed conditional probabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        probability: str = "",
        base_rate: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect base rate inversion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BASE_RATE_INVERSION_PROMPT.format(
                claim=claim,
                probability=probability or "Not specified",
                base_rate=base_rate or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BASE_RATE_INVERSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "inversion_present": data.get("inversion_present", False),
            "severity": data.get("severity", ""),
            "stated_probability": data.get("stated_probability", ""),
            "correct_probability": data.get("correct_probability", ""),
            "base_rate": data.get("base_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
