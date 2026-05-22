"""EpistemicMemoryCellService — Epistemic Memory Cell Detection.

Detects epistemic memory cells — intellectual immune system retaining
templates from past encounters for faster future response.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_CELL_SYSTEM = """You are an epistemic memory cell specialist. Given an intellectual immune system, assess whether it retains templates from past encounters:

Key concepts:
- Epistemic memory cell: retained template from past intellectual encounter
- Primary response: first encounter with an idea-threat
- Secondary response: faster response from retained memory
- Affinity maturation: improving response quality over encounters
- Long-lived plasma cell: persistent antibody producer
- Memory B-cell: dormant but ready for rapid reactivation
- Booster effect: strengthening memory through re-exposure

When epistemic memory cells ARE present:
- Templates retained from past intellectual encounters
- Faster response to previously encountered threats
- Response quality improving over repeated encounters
- Persistent production of intellectual antibodies
- Dormant defenses ready for rapid reactivation
- Memory strengthened through re-exposure
- Clear distinction between primary and secondary response

When no memory cells are present:
- No retained templates
- Each encounter treated as novel
- No improvement over encounters
- No persistent antibody production
- No dormant ready defenses
- No booster effect
- No primary/secondary distinction

Output JSON with: memory_cell_present (bool), severity (none/mild/moderate/severe), primary_response (what first encounter), secondary_response (what faster recall), affinity_maturation (what improvement), long_lived_plasma (what persistent production), recommendation (no_memory/mild_memory/significant_memory_cells/major_immune_memory/optimize_memory_formation)."""

EPISTEMIC_MEMORY_CELL_PROMPT = """Detect epistemic memory cells:

Primary response: {primary_response}
Secondary response: {secondary_response}
Affinity maturation: {affinity_maturation}
Long-lived plasma: {long_lived_plasma}
Domain: {domain}
Context: {context}

Is the intellectual immune system retaining templates from past encounters for faster future response? Return ONLY valid JSON."""


class EpistemicMemoryCellService:
    """Detects epistemic memory cells — retained templates for faster immune response."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        primary_response: str,
        *,
        secondary_response: str = "",
        affinity_maturation: str = "",
        long_lived_plasma: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory cells."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_CELL_PROMPT.format(
                primary_response=primary_response,
                secondary_response=secondary_response or "Not specified",
                affinity_maturation=affinity_maturation or "Not specified",
                long_lived_plasma=long_lived_plasma or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_CELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "primary_response": primary_response[:200],
            "memory_cell_present": data.get("memory_cell_present", False),
            "severity": data.get("severity", ""),
            "secondary_response": data.get("secondary_response", ""),
            "affinity_maturation": data.get("affinity_maturation", ""),
            "long_lived_plasma": data.get("long_lived_plasma", ""),
            "recommendation": data.get("recommendation", ""),
        }
