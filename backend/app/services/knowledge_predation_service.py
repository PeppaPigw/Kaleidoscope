"""KnowledgePredationService — Knowledge Predation Detection.

Detects knowledge predation — ideas that survive by consuming
or destroying competing ideas rather than on their own merits.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_PREDATION_SYSTEM = """You are a knowledge predation specialist. Given an intellectual ecosystem, assess whether ideas survive by consuming or destroying competitors:

Key concepts:
- Knowledge predation: ideas surviving by destroying competitors
- Idea consumption: one idea consuming another's conceptual space
- Competitive destruction: destroying rather than outcompeting
- Intellectual predation: predatory behavior in idea space
- Framework cannibalism: frameworks consuming others
- Concept colonization: concepts taking over others' territory
- Survival through destruction: surviving by eliminating alternatives

When knowledge predation IS present:
- Ideas surviving by consuming or destroying competitors
- One idea consuming another's conceptual space
- Destruction rather than fair competition
- Predatory behavior in intellectual space
- Frameworks consuming others rather than coexisting
- Concepts taking over others' legitimate territory
- Survival achieved through elimination of alternatives

When healthy competition is present:
- Ideas competing on merits
- Better ideas displacing weaker through evidence
- Competition producing refinement
- Coexistence where appropriate
- Frameworks complementing rather than consuming
- Concepts maintaining appropriate boundaries
- Survival based on explanatory power

Output JSON with: predation_present (bool), severity (none/mild/moderate/severe), ecosystem (what ecosystem exists), predator (what idea is predatory), prey (what ideas are consumed), mechanism (how predation operates), recommendation (healthy_competition/mild_displacement/significant_predation/major_idea_destruction/protect_intellectual_diversity)."""

KNOWLEDGE_PREDATION_PROMPT = """Detect knowledge predation:

Ecosystem: {ecosystem}
Predator: {predator}
Prey: {prey}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Are ideas surviving by consuming or destroying competitors? Return ONLY valid JSON."""


class KnowledgePredationService:
    """Detects knowledge predation — ideas surviving by destroying competitors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        predator: str = "",
        prey: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge predation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_PREDATION_PROMPT.format(
                ecosystem=ecosystem,
                predator=predator or "Not specified",
                prey=prey or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_PREDATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "predation_present": data.get("predation_present", False),
            "severity": data.get("severity", ""),
            "predator": data.get("predator", ""),
            "prey": data.get("prey", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
