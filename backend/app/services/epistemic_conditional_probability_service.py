"""EpistemicConditionalProbabilityService — Epistemic Conditional Probability Detection.

Detects epistemic conditional probability confusion — confusing P(A|B)
with P(B|A), the transposed conditional fallacy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONDITIONAL_PROBABILITY_SYSTEM = """You are an epistemic conditional probability specialist. Given confused conditional probabilities, assess conditional probability errors:

Key concepts:
- Epistemic conditional probability confusion: confusing P(A|B) with P(B|A)
- Transposed conditional: swapping condition and conditioned
- Prosecutor's fallacy: confusing P(evidence|innocent) with P(innocent|evidence)
- Diagnostic confusion: confusing sensitivity with positive predictive value
- Inverse probability: confusing forward and inverse probability
- Likelihood-posterior confusion: confusing likelihood with posterior
- Screening paradox: misunderstanding screening test results

When epistemic conditional probability confusion IS present:
- Conditionals transposed
- P(A|B) confused with P(B|A)
- Prosecutor's fallacy applied
- Sensitivity confused with PPV
- Forward-inverse confused
- Likelihood confused with posterior
- Screening results misunderstood

When no conditional probability confusion:
- Conditionals correctly ordered
- P(A|B) distinguished from P(B|A)
- Evidence correctly interpreted
- Sensitivity and PPV distinguished
- Forward and inverse distinguished
- Likelihood and posterior distinguished
- Screening results understood

Output JSON with: conditional_probability_confusion_detected (bool), severity (none/mild/moderate/severe), transposed_conditional (what conditionals transposed), prosecutors_fallacy (what prosecutor's fallacy), diagnostic_confusion (what diagnostic confusion), likelihood_posterior_confusion (what likelihood-posterior confused), recommendation (no_conditional_confusion/mild_direction_awareness/significant_bayesian_correction/major_intensive_probability_training/emergency_complete_conditional_confusion)."""

EPISTEMIC_CONDITIONAL_PROBABILITY_PROMPT = """Detect epistemic conditional probability confusion:

Transposed conditional: {transposed_conditional}
Prosecutor's fallacy: {prosecutors_fallacy}
Diagnostic confusion: {diagnostic_confusion}
Likelihood-posterior confusion: {likelihood_posterior_confusion}
Domain: {domain}
Context: {context}

Are conditional probabilities being confused (P(A|B) vs P(B|A))? Return ONLY valid JSON."""


class EpistemicConditionalProbabilityService:
    """Detects epistemic conditional probability confusion — transposed conditionals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        transposed_conditional: str,
        *,
        prosecutors_fallacy: str = "",
        diagnostic_confusion: str = "",
        likelihood_posterior_confusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic conditional probability confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONDITIONAL_PROBABILITY_PROMPT.format(
                transposed_conditional=transposed_conditional,
                prosecutors_fallacy=prosecutors_fallacy or "Not specified",
                diagnostic_confusion=diagnostic_confusion or "Not specified",
                likelihood_posterior_confusion=likelihood_posterior_confusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONDITIONAL_PROBABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "transposed_conditional": transposed_conditional[:200],
            "conditional_probability_confusion_detected": data.get("conditional_probability_confusion_detected", False),
            "severity": data.get("severity", ""),
            "prosecutors_fallacy": data.get("prosecutors_fallacy", ""),
            "diagnostic_confusion": data.get("diagnostic_confusion", ""),
            "likelihood_posterior_confusion": data.get("likelihood_posterior_confusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
