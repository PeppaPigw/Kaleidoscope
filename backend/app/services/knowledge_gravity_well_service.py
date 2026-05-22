"""KnowledgeGravityWellService — Knowledge Gravity Well Detection.

Detects knowledge gravity wells — established knowledge pulling all
new ideas toward it, preventing genuinely novel thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_GRAVITY_WELL_SYSTEM = """You are a knowledge gravity well specialist. Given a knowledge landscape, assess whether established knowledge is pulling all new ideas toward it:

Key concepts:
- Knowledge gravity well: established knowledge pulling new ideas toward it
- Paradigm attraction: new ideas pulled toward existing paradigm
- Novelty suppression: genuinely novel ideas suppressed by established ones
- Interpretive gravity: new data interpreted through established lens
- Framework dominance: dominant framework absorbing all new ideas
- Innovation resistance: resistance to ideas outside established gravity
- Conceptual inertia: inertia of established concepts

When knowledge gravity well IS present:
- Established knowledge pulling all new ideas toward it
- New ideas reinterpreted to fit existing paradigm
- Genuinely novel thinking suppressed
- New data always interpreted through established lens
- Dominant framework absorbing all innovation
- Ideas outside established gravity resisted
- Conceptual inertia preventing genuine novelty

When healthy knowledge integration is present:
- New ideas considered on their own merits
- Existing knowledge informing but not constraining
- Novel thinking welcomed and evaluated
- New data interpreted openly
- Frameworks updated when evidence warrants
- Innovation encouraged alongside tradition
- Conceptual flexibility maintained

Output JSON with: gravity_well_present (bool), severity (none/mild/moderate/severe), landscape (what knowledge landscape exists), established (what established knowledge dominates), new_ideas (what new ideas are affected), pull (how gravity operates), recommendation (healthy_integration/mild_paradigm_pull/significant_gravity_well/major_novelty_suppression/allow_genuinely_new_ideas)."""

KNOWLEDGE_GRAVITY_WELL_PROMPT = """Detect knowledge gravity well:

Landscape: {landscape}
Established knowledge: {established}
New ideas: {new_ideas}
Pull mechanism: {pull}
Domain: {domain}
Context: {context}

Is established knowledge pulling all new ideas toward it? Return ONLY valid JSON."""


class KnowledgeGravityWellService:
    """Detects knowledge gravity wells — established knowledge pulling new ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        landscape: str,
        *,
        established: str = "",
        new_ideas: str = "",
        pull: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge gravity well."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_GRAVITY_WELL_PROMPT.format(
                landscape=landscape,
                established=established or "Not specified",
                new_ideas=new_ideas or "Not specified",
                pull=pull or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_GRAVITY_WELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "landscape": landscape[:200],
            "gravity_well_present": data.get("gravity_well_present", False),
            "severity": data.get("severity", ""),
            "established": data.get("established", ""),
            "new_ideas": data.get("new_ideas", ""),
            "pull": data.get("pull", ""),
            "recommendation": data.get("recommendation", ""),
        }
