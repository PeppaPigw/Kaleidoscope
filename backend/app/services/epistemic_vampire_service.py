"""EpistemicVampireService — Epistemic Vampire Detection.

Detects epistemic vampirism — extracting epistemic value from
others while contributing nothing back to the knowledge commons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VAMPIRE_SYSTEM = """You are an epistemic vampire specialist. Given a knowledge-sharing interaction, assess whether someone is extracting epistemic value without contributing:

Key concepts:
- Epistemic vampirism: extracting knowledge value without contributing
- One-way knowledge extraction: taking knowledge without giving
- Epistemic free-riding: benefiting from others' epistemic labor
- Knowledge exploitation: exploiting others' knowledge work
- Asymmetric extraction: taking more than contributing
- Epistemic drain: draining others' epistemic resources
- Contribution avoidance: systematically avoiding contribution

When epistemic vampirism IS present:
- Knowledge extracted without reciprocation
- Epistemic labor exploited without acknowledgment
- One-way extraction pattern established
- Contribution systematically avoided
- Others' epistemic resources drained
- Knowledge taken without sustaining the source
- Free-riding on collective epistemic work

When appropriate knowledge use is present:
- Knowledge shared and received reciprocally
- Epistemic labor acknowledged and valued
- Contribution proportionate to extraction
- Knowledge commons sustained by participants
- Resources shared sustainably
- Learning and teaching balanced

Output JSON with: vampire_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), extraction (what is extracted), contribution (what is contributed), asymmetry (how extraction exceeds contribution), recommendation (balanced_exchange/mild_asymmetry/significant_epistemic_vampirism/major_knowledge_exploitation/contribute_reciprocally)."""

EPISTEMIC_VAMPIRE_PROMPT = """Detect epistemic vampirism:

Interaction: {interaction}
Extraction: {extraction}
Contribution: {contribution}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Is epistemic value being extracted without contributing back? Return ONLY valid JSON."""


class EpistemicVampireService:
    """Detects epistemic vampirism — extracting value without contributing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        extraction: str = "",
        contribution: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vampirism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VAMPIRE_PROMPT.format(
                interaction=interaction,
                extraction=extraction or "Not specified",
                contribution=contribution or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VAMPIRE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "vampire_present": data.get("vampire_present", False),
            "severity": data.get("severity", ""),
            "extraction": data.get("extraction", ""),
            "contribution": data.get("contribution", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
