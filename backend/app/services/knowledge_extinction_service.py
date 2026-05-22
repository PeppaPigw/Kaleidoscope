"""KnowledgeExtinctionService — Knowledge Extinction Detection.

Detects knowledge extinction — the loss of knowledge traditions,
practices, or ways of knowing that cannot be recovered once gone,
reducing humanity's epistemic resources.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_EXTINCTION_SYSTEM = """You are a knowledge extinction specialist. Given a knowledge domain, assess whether valuable knowledge is being lost:

Key concepts:
- Knowledge extinction: irreversible loss of ways of knowing
- Epistemic loss: knowledge that cannot be reconstructed
- Tradition death: loss of knowledge-bearing practices
- Tacit knowledge loss: embodied knowledge that dies with practitioners
- Language death: loss of concepts encoded in dying languages
- Practice extinction: loss of knowledge embedded in practice
- Epistemic impoverishment: reduced capacity to know

When knowledge extinction IS present:
- Valuable knowledge being irreversibly lost
- Knowledge traditions dying without documentation
- Tacit knowledge disappearing with practitioners
- Concepts being lost with dying languages
- Practices carrying knowledge being abandoned
- No effort to preserve endangered knowledge
- Loss reduces humanity's epistemic capacity

When knowledge evolution is appropriate:
- Outdated knowledge replaced by better knowledge
- Loss is of genuinely superseded approaches
- Core insights preserved even as forms change
- Knowledge transformed rather than lost
- Practitioners choose to evolve their practice
- Documentation preserves what's valuable
- Change serves epistemic progress

Output JSON with: extinction_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge is at risk), tradition (what tradition carries it), threat (what threatens it), irreversibility (how irreversible the loss), recommendation (appropriate_knowledge_evolution/mild_tradition_erosion/significant_knowledge_extinction/major_epistemic_loss/preserve_endangered_knowledge)."""

KNOWLEDGE_EXTINCTION_PROMPT = """Detect knowledge extinction:

Knowledge at risk: {knowledge}
Tradition: {tradition}
Threat: {threat}
Preservation efforts: {preservation}
Domain: {domain}
Context: {context}

Is valuable knowledge being irreversibly lost? Return ONLY valid JSON."""


class KnowledgeExtinctionService:
    """Detects knowledge extinction — irreversible loss of ways of knowing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        tradition: str = "",
        threat: str = "",
        preservation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge extinction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_EXTINCTION_PROMPT.format(
                knowledge=knowledge,
                tradition=tradition or "Not specified",
                threat=threat or "Not specified",
                preservation=preservation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_EXTINCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "extinction_present": data.get("extinction_present", False),
            "severity": data.get("severity", ""),
            "tradition": data.get("tradition", ""),
            "threat": data.get("threat", ""),
            "irreversibility": data.get("irreversibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
