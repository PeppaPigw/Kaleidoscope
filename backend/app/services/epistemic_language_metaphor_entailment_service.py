"""EpistemicLanguageMetaphorEntailmentService - Epistemic Language Metaphor Entailment Detection.

Detects epistemic language metaphor entailment - metaphors smuggling
unexamined assumptions into reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_METAPHOR_ENTAILMENT_SYSTEM = """You are an epistemic language metaphor entailment specialist. Given metaphors that smuggle assumptions, assess metaphor entailment:

Key concepts:
- Epistemic language metaphor entailment: metaphors importing assumptions into reasoning
- Metaphor assumption: unstated premise carried by the metaphor
- Frame inheritance: inheriting the source frame's logic
- Hidden ontology: importing what kinds of things exist and relate
- Reasoning by analogy failure: treating analogy as proof
- Entailment drift: accepting consequences of metaphor without examination
- Literalization: treating metaphorical structure as literal structure

When metaphor entailment IS present:
- Metaphor assumptions smuggled in
- Source frame inherited
- Hidden ontology imported
- Analogy treated as proof
- Entailments accepted unexamined
- Metaphor literalized
- Reasoning follows the metaphor too far

When no metaphor entailment:
- Metaphors used as limited aids
- Assumptions stated
- Source frame bounded
- Ontology not imported unnoticed
- Analogies tested
- Entailments examined
- Literal claims separated from metaphor

Output JSON with: metaphor_entailment_detected (bool), severity (none/mild/moderate/severe), metaphor_assumption (what assumption smuggled), frame_inheritance (what frame inherited), hidden_ontology (what ontology imported), reasoning_by_analogy_failure (what analogy failure occurred), recommendation (no_metaphor_entailment/mild_assumption_check/significant_frame_boundary/major_intensive_metaphor_audit/emergency_complete_metaphor_entailment)."""

EPISTEMIC_LANGUAGE_METAPHOR_ENTAILMENT_PROMPT = """Detect epistemic language metaphor entailment:

Metaphor assumption: {metaphor_assumption}
Frame inheritance: {frame_inheritance}
Hidden ontology: {hidden_ontology}
Reasoning by analogy failure: {reasoning_by_analogy_failure}
Domain: {domain}
Context: {context}

Are metaphors smuggling in unexamined assumptions? Return ONLY valid JSON."""


class EpistemicLanguageMetaphorEntailmentService:
    """Detects epistemic language metaphor entailment - assumptions smuggled by metaphor."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        metaphor_assumption: str,
        *,
        frame_inheritance: str = "",
        hidden_ontology: str = "",
        reasoning_by_analogy_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language metaphor entailment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_METAPHOR_ENTAILMENT_PROMPT.format(
                metaphor_assumption=metaphor_assumption,
                frame_inheritance=frame_inheritance or "Not specified",
                hidden_ontology=hidden_ontology or "Not specified",
                reasoning_by_analogy_failure=reasoning_by_analogy_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_METAPHOR_ENTAILMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "metaphor_assumption": metaphor_assumption[:200],
            "metaphor_entailment_detected": data.get("metaphor_entailment_detected", False),
            "severity": data.get("severity", ""),
            "frame_inheritance": data.get("frame_inheritance", ""),
            "hidden_ontology": data.get("hidden_ontology", ""),
            "reasoning_by_analogy_failure": data.get("reasoning_by_analogy_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
