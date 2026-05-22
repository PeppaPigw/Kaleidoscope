"""EpistemicMetaphorEntrapmentService — Epistemic Metaphor Entrapment Detection.

Detects epistemic metaphor entrapment — being trapped by a metaphor
that constrains thinking and prevents seeing alternatives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METAPHOR_ENTRAPMENT_SYSTEM = """You are an epistemic metaphor entrapment specialist. Given metaphors that constrain thinking, assess metaphor entrapment:

Key concepts:
- Epistemic metaphor entrapment: trapped by a metaphor constraining thinking
- Conceptual prison: metaphor becomes a prison for thought
- Alternative blindness: metaphor prevents seeing alternatives
- Inference inheritance: inheriting inferences from metaphor that don't apply
- Emotional loading: metaphor carries emotional weight that biases
- Structural constraint: metaphor's structure constrains solution space
- Dead metaphor activation: dead metaphors still constraining thinking unconsciously

When epistemic metaphor entrapment IS present:
- Trapped by metaphor
- Thinking constrained
- Alternatives not visible
- False inferences inherited
- Emotional loading biasing
- Solution space constrained
- Dead metaphors still active

When no metaphor entrapment:
- Metaphors used as tools not prisons
- Thinking flexible beyond metaphor
- Alternatives visible
- Inferences checked against reality
- Emotional loading recognized
- Solution space open
- Metaphors consciously chosen

Output JSON with: metaphor_entrapment_detected (bool), severity (none/mild/moderate/severe), conceptual_prison (what metaphor imprisons), alternative_blindness (what alternatives hidden), inference_inheritance (what false inferences), structural_constraint (what constrained), recommendation (no_metaphor_entrapment/mild_metaphor_awareness/significant_alternative_metaphors/major_intensive_metaphor_liberation/emergency_complete_metaphor_entrapment)."""

EPISTEMIC_METAPHOR_ENTRAPMENT_PROMPT = """Detect epistemic metaphor entrapment:

Conceptual prison: {conceptual_prison}
Alternative blindness: {alternative_blindness}
Inference inheritance: {inference_inheritance}
Structural constraint: {structural_constraint}
Domain: {domain}
Context: {context}

Is thinking being trapped by a constraining metaphor? Return ONLY valid JSON."""


class EpistemicMetaphorEntrapmentService:
    """Detects epistemic metaphor entrapment — metaphor as prison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conceptual_prison: str,
        *,
        alternative_blindness: str = "",
        inference_inheritance: str = "",
        structural_constraint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metaphor entrapment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METAPHOR_ENTRAPMENT_PROMPT.format(
                conceptual_prison=conceptual_prison,
                alternative_blindness=alternative_blindness or "Not specified",
                inference_inheritance=inference_inheritance or "Not specified",
                structural_constraint=structural_constraint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METAPHOR_ENTRAPMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conceptual_prison": conceptual_prison[:200],
            "metaphor_entrapment_detected": data.get("metaphor_entrapment_detected", False),
            "severity": data.get("severity", ""),
            "alternative_blindness": data.get("alternative_blindness", ""),
            "inference_inheritance": data.get("inference_inheritance", ""),
            "structural_constraint": data.get("structural_constraint", ""),
            "recommendation": data.get("recommendation", ""),
        }
