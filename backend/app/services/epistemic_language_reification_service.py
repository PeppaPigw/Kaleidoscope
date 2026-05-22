"""EpistemicLanguageReificationService — Epistemic Language Reification Detection.

Detects epistemic language reification — treating abstract concepts as
concrete things, confusing the map for the territory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_REIFICATION_SYSTEM = """You are an epistemic language reification specialist. Given treating abstractions as concrete things, assess language reification:

Key concepts:
- Epistemic language reification: treating abstract concepts as concrete things
- Concept concretization: making abstract concepts seem concrete
- Category as entity: treating categories as real entities
- Process as thing: treating processes as static things
- Relation as substance: treating relations as substances
- Pattern as object: treating patterns as physical objects
- Model as reality: treating models as reality itself

When epistemic language reification IS present:
- Abstractions treated as concrete
- Concepts concretized
- Categories treated as entities
- Processes treated as things
- Relations treated as substances
- Patterns treated as objects
- Models treated as reality

When no language reification:
- Abstractions recognized as abstract
- Concepts held lightly
- Categories seen as tools
- Processes seen as dynamic
- Relations seen as relational
- Patterns seen as patterns
- Models seen as models

Output JSON with: language_reification_detected (bool), severity (none/mild/moderate/severe), concept_concretization (what concepts concretized), category_as_entity (what categories treated as entities), process_as_thing (what processes treated as things), model_as_reality (what models treated as reality), recommendation (no_language_reification/mild_abstraction_awareness/significant_concept_flexibility/major_intensive_language_deconstructing/emergency_complete_language_reification)."""

EPISTEMIC_LANGUAGE_REIFICATION_PROMPT = """Detect epistemic language reification:

Concept concretization: {concept_concretization}
Category as entity: {category_as_entity}
Process as thing: {process_as_thing}
Model as reality: {model_as_reality}
Domain: {domain}
Context: {context}

Are abstract concepts being treated as concrete things? Return ONLY valid JSON."""


class EpistemicLanguageReificationService:
    """Detects epistemic language reification — treating abstractions as concrete."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        concept_concretization: str,
        *,
        category_as_entity: str = "",
        process_as_thing: str = "",
        model_as_reality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language reification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_REIFICATION_PROMPT.format(
                concept_concretization=concept_concretization,
                category_as_entity=category_as_entity or "Not specified",
                process_as_thing=process_as_thing or "Not specified",
                model_as_reality=model_as_reality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_REIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "concept_concretization": concept_concretization[:200],
            "language_reification_detected": data.get("language_reification_detected", False),
            "severity": data.get("severity", ""),
            "category_as_entity": data.get("category_as_entity", ""),
            "process_as_thing": data.get("process_as_thing", ""),
            "model_as_reality": data.get("model_as_reality", ""),
            "recommendation": data.get("recommendation", ""),
        }
