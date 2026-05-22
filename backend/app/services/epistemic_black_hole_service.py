"""EpistemicBlackHoleService — Epistemic Black Hole Detection.

Detects epistemic black holes — ideas so dominant they absorb all
surrounding discourse, preventing other ideas from being considered.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BLACK_HOLE_SYSTEM = """You are an epistemic black hole specialist. Given a discourse environment, assess whether dominant ideas are absorbing all surrounding discourse:

Key concepts:
- Epistemic black hole: idea so dominant it absorbs all discourse
- Discourse absorption: all discussion pulled toward one idea
- Idea dominance: one idea dominating all others
- Alternative suppression: alternatives suppressed by dominant idea
- Gravitational pull: dominant idea pulling all thought toward it
- Escape velocity: difficulty of escaping dominant idea's pull
- Discourse collapse: discourse collapsing into single point

When epistemic black hole IS present:
- Dominant idea absorbing all surrounding discourse
- All discussion pulled toward one central idea
- One idea dominating to exclusion of all others
- Alternative ideas suppressed by dominant one
- Gravitational pull preventing consideration of alternatives
- Escape from dominant idea's influence nearly impossible
- Discourse collapsing into single perspective

When healthy idea prominence is present:
- Important ideas prominent but not exclusive
- Discussion focused but open to alternatives
- Dominant ideas coexisting with others
- Alternatives considered alongside main idea
- Prominence proportionate to evidence
- Other perspectives accessible
- Discourse maintaining diversity

Output JSON with: black_hole_present (bool), severity (none/mild/moderate/severe), environment (what environment is affected), dominant_idea (what idea dominates), absorption (what is absorbed), alternatives_lost (what alternatives are lost), recommendation (healthy_prominence/mild_dominance/significant_epistemic_black_hole/major_discourse_collapse/maintain_idea_diversity)."""

EPISTEMIC_BLACK_HOLE_PROMPT = """Detect epistemic black hole:

Environment: {environment}
Dominant idea: {dominant}
Absorption: {absorption}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is a dominant idea absorbing all surrounding discourse? Return ONLY valid JSON."""


class EpistemicBlackHoleService:
    """Detects epistemic black holes — ideas absorbing all discourse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        dominant: str = "",
        absorption: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic black hole."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BLACK_HOLE_PROMPT.format(
                environment=environment,
                dominant=dominant or "Not specified",
                absorption=absorption or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BLACK_HOLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "black_hole_present": data.get("black_hole_present", False),
            "severity": data.get("severity", ""),
            "dominant_idea": data.get("dominant_idea", ""),
            "absorption": data.get("absorption", ""),
            "alternatives_lost": data.get("alternatives_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
