"""EpistemicInferenceSuppressionService — Epistemic Inference Suppression Detection.

Detects epistemic inference suppression — suppressing valid inferences
that lead to uncomfortable or inconvenient conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFERENCE_SUPPRESSION_SYSTEM = """You are an epistemic inference suppression specialist. Given suppressed valid inferences, assess inference suppression:

Key concepts:
- Epistemic inference suppression: suppressing valid inferences to uncomfortable conclusions
- Motivated non-inference: refusing to draw obvious conclusions
- Willful obtuseness: pretending not to see what follows
- Conclusion avoidance: avoiding drawing warranted conclusions
- Implication denial: denying implications of accepted premises
- Logical cowardice: lacking courage to follow logic where it leads
- Strategic ignorance of implications: strategically ignoring what follows

When epistemic inference suppression IS present:
- Valid inferences suppressed
- Obvious conclusions refused
- Obtuseness willful
- Conclusions avoided
- Implications denied
- Logic not followed
- Implications strategically ignored

When no inference suppression:
- Valid inferences drawn
- Conclusions accepted
- Implications acknowledged
- Logic followed
- Uncomfortable truths faced
- Courage to conclude
- Implications explored

Output JSON with: inference_suppression_detected (bool), severity (none/mild/moderate/severe), motivated_non_inference (what inferences refused), conclusion_avoidance (what conclusions avoided), implication_denial (what implications denied), logical_cowardice (what logic not followed), recommendation (no_inference_suppression/mild_courage_practice/significant_implication_facing/major_intensive_conclusion_drawing/emergency_complete_inference_suppression)."""

EPISTEMIC_INFERENCE_SUPPRESSION_PROMPT = """Detect epistemic inference suppression:

Motivated non-inference: {motivated_non_inference}
Conclusion avoidance: {conclusion_avoidance}
Implication denial: {implication_denial}
Logical cowardice: {logical_cowardice}
Domain: {domain}
Context: {context}

Are valid inferences being suppressed because they lead to uncomfortable conclusions? Return ONLY valid JSON."""


class EpistemicInferenceSuppressionService:
    """Detects epistemic inference suppression — valid conclusions avoided."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        motivated_non_inference: str,
        *,
        conclusion_avoidance: str = "",
        implication_denial: str = "",
        logical_cowardice: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inference suppression."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFERENCE_SUPPRESSION_PROMPT.format(
                motivated_non_inference=motivated_non_inference,
                conclusion_avoidance=conclusion_avoidance or "Not specified",
                implication_denial=implication_denial or "Not specified",
                logical_cowardice=logical_cowardice or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFERENCE_SUPPRESSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "motivated_non_inference": motivated_non_inference[:200],
            "inference_suppression_detected": data.get("inference_suppression_detected", False),
            "severity": data.get("severity", ""),
            "conclusion_avoidance": data.get("conclusion_avoidance", ""),
            "implication_denial": data.get("implication_denial", ""),
            "logical_cowardice": data.get("logical_cowardice", ""),
            "recommendation": data.get("recommendation", ""),
        }
