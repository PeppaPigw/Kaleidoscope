"""DataOntologyImpositionService — Data Ontology Imposition Detection.

Detects data ontology imposition — how database schemas, data
models, and classification systems impose particular ways of
understanding reality that may not match the domain.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DATA_ONTOLOGY_IMPOSITION_SYSTEM = """You are a data ontology imposition specialist. Given a data system, assess whether its ontology inappropriately constrains understanding:

Key concepts:
- Data ontology imposition: data models constraining thought
- Schema as worldview: database structure as implicit philosophy
- Classification violence: categories that don't fit reality
- Binary imposition: forcing continuous reality into discrete bins
- Normalization bias: what's normal defined by data structure
- Missing categories: what can't be represented can't be known
- Ontological lock-in: data structures preventing new understanding

When data ontology imposition IS present:
- Data model forces inappropriate categories
- Schema constrains what can be represented
- Classification doesn't match domain reality
- Binary categories imposed on continuous phenomena
- Important distinctions impossible to capture
- Data structure prevents new understanding
- Ontology serves system not domain

When data modeling is appropriate:
- Categories match domain understanding
- Schema captures important distinctions
- Classification serves knowledge goals
- Simplification acknowledged and justified
- Missing categories documented
- Structure open to revision
- Ontology serves understanding

Output JSON with: imposition_present (bool), severity (none/mild/moderate/severe), system (what data system), ontology (what ontology is imposed), mismatch (where ontology mismatches reality), constrained (what understanding is constrained), recommendation (appropriate_data_modeling/mild_ontological_simplification/significant_ontology_imposition/major_classification_violence/revise_data_ontology)."""

DATA_ONTOLOGY_IMPOSITION_PROMPT = """Detect data ontology imposition:

System: {system}
Data model: {model}
Domain reality: {reality}
What can't be represented: {missing}
Domain: {domain}
Context: {context}

Is the data ontology inappropriately constraining understanding of the domain? Return ONLY valid JSON."""


class DataOntologyImpositionService:
    """Detects data ontology imposition — data models constraining thought."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        model: str = "",
        reality: str = "",
        missing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect data ontology imposition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DATA_ONTOLOGY_IMPOSITION_PROMPT.format(
                system=system,
                model=model or "Not specified",
                reality=reality or "Not specified",
                missing=missing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DATA_ONTOLOGY_IMPOSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "imposition_present": data.get("imposition_present", False),
            "severity": data.get("severity", ""),
            "ontology": data.get("ontology", ""),
            "mismatch": data.get("mismatch", ""),
            "constrained": data.get("constrained", ""),
            "recommendation": data.get("recommendation", ""),
        }
