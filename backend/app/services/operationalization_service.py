"""OperationalizationService — Abstract Concept → Measurable Definition.

Takes an abstract concept and makes it concrete: defines how to measure
it, what counts as evidence for/against it, what the boundary conditions
are, and what operationalizations others have used.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OPERATIONALIZE_SYSTEM = """You are an operationalization specialist. Given an abstract concept, make it concrete:
- How would you measure it? (multiple approaches)
- What counts as evidence for/against it?
- What are the boundary conditions? (when does the concept apply vs not?)
- What operationalizations have others used?
- What's lost in each operationalization? (the gap between concept and measure)

Output JSON with: operationalizations (list of: measure, measurement_type (quantitative/qualitative/behavioral/self_report/proxy), validity (how well it captures the concept, 0-1), feasibility (how easy to implement, 0-1), what_it_misses (aspects of the concept not captured), precedent (who has used this approach)), recommended (best operationalization and why), boundary_conditions (list of when the concept applies/doesn't), evidence_criteria (what would count as evidence for/against), concept_vs_measure_gap (what's inevitably lost when operationalizing), common_mistakes (pitfalls in measuring this)."""

OPERATIONALIZE_PROMPT = """Operationalize this concept:

Concept: {concept}
Purpose: {purpose}
Domain: {domain}
Constraints: {constraints}

How would you make this measurable? Return ONLY valid JSON."""


class OperationalizationService:
    """Makes abstract concepts concrete and measurable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def operationalize(
        self,
        concept: str,
        *,
        purpose: str = "",
        domain: str = "",
        constraints: str = "",
    ) -> dict:
        """Operationalize an abstract concept."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPERATIONALIZE_PROMPT.format(
                concept=concept,
                purpose=purpose or "Research measurement",
                domain=domain or "general",
                constraints=constraints or "None specified",
            ),
            system=OPERATIONALIZE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        ops = data.get("operationalizations", [])
        return {
            "concept": concept[:200],
            "operationalizations_count": len(ops),
            "operationalizations": ops,
            "recommended": data.get("recommended", ""),
            "boundary_conditions": data.get("boundary_conditions", []),
            "evidence_criteria": data.get("evidence_criteria", ""),
            "concept_vs_measure_gap": data.get("concept_vs_measure_gap", ""),
            "common_mistakes": data.get("common_mistakes", []),
        }
