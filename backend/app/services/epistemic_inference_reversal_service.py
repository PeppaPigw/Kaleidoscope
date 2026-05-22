"""EpistemicInferenceReversalService — Epistemic Inference Reversal Detection.

Detects epistemic inference reversal — reversing the direction of valid
inference, confusing what follows from what.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFERENCE_REVERSAL_SYSTEM = """You are an epistemic inference reversal specialist. Given reversed inference direction, assess inference reversal:

Key concepts:
- Epistemic inference reversal: reversing direction of valid inference
- Affirming consequent: if P then Q, Q therefore P
- Inverse error: confusing a statement with its inverse
- Conditional reversal: reversing conditional direction
- Probability inversion: confusing P(A|B) with P(B|A)
- Explanation-prediction confusion: confusing what explains with what predicts
- Diagnostic reversal: reversing diagnostic reasoning direction

When epistemic inference reversal IS present:
- Inference direction reversed
- Consequent affirmed
- Inverse confused
- Conditionals reversed
- Probabilities inverted
- Explanation-prediction confused
- Diagnostic direction wrong

When no inference reversal:
- Inference direction correct
- Modus ponens valid
- Statement and inverse distinguished
- Conditionals correct
- Probabilities ordered correctly
- Explanation and prediction distinguished
- Diagnostic direction correct

Output JSON with: inference_reversal_detected (bool), severity (none/mild/moderate/severe), affirming_consequent (what consequent affirmed), conditional_reversal (what conditionals reversed), probability_inversion (what probabilities inverted), diagnostic_reversal (what diagnostics reversed), recommendation (no_inference_reversal/mild_direction_checking/significant_logic_correction/major_intensive_inference_repair/emergency_complete_inference_reversal)."""

EPISTEMIC_INFERENCE_REVERSAL_PROMPT = """Detect epistemic inference reversal:

Affirming consequent: {affirming_consequent}
Conditional reversal: {conditional_reversal}
Probability inversion: {probability_inversion}
Diagnostic reversal: {diagnostic_reversal}
Domain: {domain}
Context: {context}

Is the direction of valid inference being reversed? Return ONLY valid JSON."""


class EpistemicInferenceReversalService:
    """Detects epistemic inference reversal — direction confusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        affirming_consequent: str,
        *,
        conditional_reversal: str = "",
        probability_inversion: str = "",
        diagnostic_reversal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inference reversal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFERENCE_REVERSAL_PROMPT.format(
                affirming_consequent=affirming_consequent,
                conditional_reversal=conditional_reversal or "Not specified",
                probability_inversion=probability_inversion or "Not specified",
                diagnostic_reversal=diagnostic_reversal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFERENCE_REVERSAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "affirming_consequent": affirming_consequent[:200],
            "inference_reversal_detected": data.get("inference_reversal_detected", False),
            "severity": data.get("severity", ""),
            "conditional_reversal": data.get("conditional_reversal", ""),
            "probability_inversion": data.get("probability_inversion", ""),
            "diagnostic_reversal": data.get("diagnostic_reversal", ""),
            "recommendation": data.get("recommendation", ""),
        }
