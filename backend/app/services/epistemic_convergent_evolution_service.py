"""EpistemicConvergentEvolutionService — Epistemic Convergent Evolution Detection.

Detects epistemic convergent evolution — unrelated ideas independently
arriving at the same solution through different paths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONVERGENT_EVOLUTION_SYSTEM = """You are an epistemic convergent evolution specialist. Given intellectual solutions, assess whether unrelated ideas independently arrived at the same answer:

Key concepts:
- Epistemic convergent evolution: unrelated ideas reaching same solution
- Analogous structure: similar function from different origins
- Selection pressure: common problem driving similar solutions
- Independent origin: no shared ancestry for the solution
- Functional constraint: limited ways to solve the problem
- Deep homology: shared deep mechanism despite surface difference
- Parallel evolution: related ideas evolving same trait independently

When epistemic convergent evolution IS present:
- Unrelated ideas independently arriving at same solution
- Similar intellectual function from different origins
- Common problem driving similar solutions
- No shared ancestry for the convergent solution
- Limited ways to solve the intellectual problem
- Possible shared deep mechanism
- Related ideas evolving same trait independently

When shared ancestry is present:
- Similar solutions from common origin
- Homologous structures from shared ancestor
- No independent arrival
- Clear shared ancestry
- Many possible solutions
- Surface similarity from common origin
- Single evolutionary event

Output JSON with: convergent_evolution_present (bool), severity (none/mild/moderate/severe), analogous_structure (what similar function), selection_pressure (what common problem), independent_origin (what separate paths), functional_constraint (what limited solutions), recommendation (shared_ancestry/mild_convergence/significant_convergent_evolution/major_independent_convergence/identify_selection_pressure)."""

EPISTEMIC_CONVERGENT_EVOLUTION_PROMPT = """Detect epistemic convergent evolution:

Analogous structure: {analogous_structure}
Selection pressure: {selection_pressure}
Independent origin: {independent_origin}
Functional constraint: {functional_constraint}
Domain: {domain}
Context: {context}

Are unrelated ideas independently arriving at the same solution through different paths? Return ONLY valid JSON."""


class EpistemicConvergentEvolutionService:
    """Detects epistemic convergent evolution — unrelated ideas reaching same solution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        analogous_structure: str,
        *,
        selection_pressure: str = "",
        independent_origin: str = "",
        functional_constraint: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic convergent evolution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONVERGENT_EVOLUTION_PROMPT.format(
                analogous_structure=analogous_structure,
                selection_pressure=selection_pressure or "Not specified",
                independent_origin=independent_origin or "Not specified",
                functional_constraint=functional_constraint or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONVERGENT_EVOLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "analogous_structure": analogous_structure[:200],
            "convergent_evolution_present": data.get("convergent_evolution_present", False),
            "severity": data.get("severity", ""),
            "selection_pressure": data.get("selection_pressure", ""),
            "independent_origin": data.get("independent_origin", ""),
            "functional_constraint": data.get("functional_constraint", ""),
            "recommendation": data.get("recommendation", ""),
        }
