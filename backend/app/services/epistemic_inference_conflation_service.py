"""EpistemicInferenceConflationService — Epistemic Inference Conflation Detection.

Detects epistemic inference conflation — conflating different types of
inference (deductive, inductive, abductive) inappropriately.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFERENCE_CONFLATION_SYSTEM = """You are an epistemic inference conflation specialist. Given conflated inference types, assess inference conflation:

Key concepts:
- Epistemic inference conflation: conflating different inference types
- Deductive-inductive confusion: treating inductive conclusions as deductively certain
- Abductive overcertainty: treating best explanation as proven fact
- Analogical-deductive confusion: treating analogical reasoning as deductive proof
- Statistical-individual confusion: applying statistical inference to individuals
- Correlation-causation conflation: treating correlation as causal inference
- Possibility-probability conflation: treating mere possibility as probable

When epistemic inference conflation IS present:
- Inference types conflated
- Inductive treated as deductive
- Abductive treated as proven
- Analogical treated as proof
- Statistical applied to individual
- Correlation treated as causation
- Possibility treated as probability

When no inference conflation:
- Inference types distinguished
- Inductive uncertainty acknowledged
- Abductive tentativeness maintained
- Analogical limits recognized
- Statistical-individual distinction maintained
- Correlation-causation distinguished
- Possibility-probability distinguished

Output JSON with: inference_conflation_detected (bool), severity (none/mild/moderate/severe), deductive_inductive_confusion (what confused), abductive_overcertainty (what overcertain), statistical_individual_confusion (what confused), possibility_probability_conflation (what conflated), recommendation (no_inference_conflation/mild_type_awareness/significant_inference_typing/major_intensive_logic_separation/emergency_complete_inference_conflation)."""

EPISTEMIC_INFERENCE_CONFLATION_PROMPT = """Detect epistemic inference conflation:

Deductive-inductive confusion: {deductive_inductive_confusion}
Abductive overcertainty: {abductive_overcertainty}
Statistical-individual confusion: {statistical_individual_confusion}
Possibility-probability conflation: {possibility_probability_conflation}
Domain: {domain}
Context: {context}

Are different types of inference being conflated inappropriately? Return ONLY valid JSON."""


class EpistemicInferenceConflationService:
    """Detects epistemic inference conflation — type confusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deductive_inductive_confusion: str,
        *,
        abductive_overcertainty: str = "",
        statistical_individual_confusion: str = "",
        possibility_probability_conflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inference conflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFERENCE_CONFLATION_PROMPT.format(
                deductive_inductive_confusion=deductive_inductive_confusion,
                abductive_overcertainty=abductive_overcertainty or "Not specified",
                statistical_individual_confusion=statistical_individual_confusion or "Not specified",
                possibility_probability_conflation=possibility_probability_conflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFERENCE_CONFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deductive_inductive_confusion": deductive_inductive_confusion[:200],
            "inference_conflation_detected": data.get("inference_conflation_detected", False),
            "severity": data.get("severity", ""),
            "abductive_overcertainty": data.get("abductive_overcertainty", ""),
            "statistical_individual_confusion": data.get("statistical_individual_confusion", ""),
            "possibility_probability_conflation": data.get("possibility_probability_conflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
