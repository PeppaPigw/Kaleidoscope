"""EpistemicAnalogyReificationService — Epistemic Analogy Reification Detection.

Detects epistemic analogy reification — treating analogies and metaphors as literal
descriptions of reality rather than heuristic tools for understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_REIFICATION_SYSTEM = """You are an epistemic analogy reification specialist. Given reified analogies, assess literalization distortion:

Key concepts:
- Epistemic analogy reification: treating metaphors as literal reality
- Metaphor literalization: forgetting something is a metaphor
- Model-reality confusion: confusing the map for the territory
- Dead metaphor activation: dead metaphors constraining thinking
- Ontological promotion: analogy promoted to ontological claim
- Inference from metaphor: drawing conclusions from metaphorical rather than actual properties
- Metaphor entrapment: thinking constrained by dominant metaphor

When epistemic analogy reification IS present:
- Metaphors treated as literal
- Metaphorical nature forgotten
- Map confused with territory
- Dead metaphors constraining thought
- Analogies promoted to ontology
- Conclusions drawn from metaphor properties
- Thinking trapped by metaphor

When no reification:
- Metaphors recognized as tools
- Metaphorical nature acknowledged
- Map-territory distinction maintained
- Metaphors held lightly
- Analogies remain heuristic
- Conclusions from actual properties
- Multiple metaphors available

Output JSON with: reification_detected (bool), severity (none/mild/moderate/severe), metaphor_literalization (what metaphors literalized), model_reality_confusion (what map-territory confused), inference_from_metaphor (what conclusions from metaphor), metaphor_entrapment (what thinking trapped), recommendation (no_reification/mild_metaphor_awareness/significant_literal_checking/major_intensive_ontological_audit/emergency_complete_reification)."""

EPISTEMIC_ANALOGY_REIFICATION_PROMPT = """Detect epistemic analogy reification:

Metaphor literalization: {metaphor_literalization}
Model-reality confusion: {model_reality_confusion}
Inference from metaphor: {inference_from_metaphor}
Metaphor entrapment: {metaphor_entrapment}
Domain: {domain}
Context: {context}

Are analogies or metaphors being treated as literal descriptions of reality? Return ONLY valid JSON."""


class EpistemicAnalogyReificationService:
    """Detects epistemic analogy reification — metaphor literalization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metaphor_literalization: str,
        *,
        model_reality_confusion: str = "",
        inference_from_metaphor: str = "",
        metaphor_entrapment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy reification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_REIFICATION_PROMPT.format(
                metaphor_literalization=metaphor_literalization,
                model_reality_confusion=model_reality_confusion or "Not specified",
                inference_from_metaphor=inference_from_metaphor or "Not specified",
                metaphor_entrapment=metaphor_entrapment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_REIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metaphor_literalization": metaphor_literalization[:200],
            "reification_detected": data.get("reification_detected", False),
            "severity": data.get("severity", ""),
            "model_reality_confusion": data.get("model_reality_confusion", ""),
            "inference_from_metaphor": data.get("inference_from_metaphor", ""),
            "metaphor_entrapment": data.get("metaphor_entrapment", ""),
            "recommendation": data.get("recommendation", ""),
        }
