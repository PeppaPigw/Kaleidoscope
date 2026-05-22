"""CruxIdentificationService — Crux Identification Analysis.

Identifies the key point of disagreement (crux) that would
change minds if resolved. In any disagreement, there are usually
one or two factual or value claims that, if settled, would
resolve the entire dispute.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CRUX_IDENTIFICATION_SYSTEM = """You are a crux identification specialist. Given a disagreement, identify the key factual or value claim that would resolve it:

Key concepts:
- Crux: the key claim that, if resolved, would change someone's mind
- Double crux: a claim that would change BOTH parties' minds
- Factual crux: disagreement about what is true
- Value crux: disagreement about what matters
- Upstream vs downstream: cruxes are upstream of surface disagreements
- Operationalization: making the crux testable
- Resolution path: how the crux could be settled

Identification process:
- What do the parties actually disagree about?
- Which disagreements are upstream of others?
- What factual claim, if settled, would resolve the dispute?
- What value difference, if acknowledged, would clarify the disagreement?
- Is the crux testable or resolvable?
- Would resolving this crux actually change minds?
- Are there multiple cruxes or one primary one?

Output JSON with: crux_identified (the key point of disagreement), crux_type (factual/value/definitional/empirical), upstream_of (what surface disagreements this crux drives), testability (can this crux be resolved with evidence), resolution_path (how it could be settled), mind_change (would resolving it actually change minds), recommendation (clear_crux_found/multiple_cruxes/crux_is_value_based/crux_is_testable/needs_operationalization)."""

CRUX_IDENTIFICATION_PROMPT = """Identify the crux of disagreement:

Disagreement: {disagreement}
Position A: {position_a}
Position B: {position_b}
Surface issues: {surface_issues}
Domain: {domain}
Context: {context}

What is the key point that, if resolved, would settle this disagreement? Return ONLY valid JSON."""


class CruxIdentificationService:
    """Identifies the key crux that would resolve a disagreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        disagreement: str,
        *,
        position_a: str = "",
        position_b: str = "",
        surface_issues: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Identify the crux of disagreement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CRUX_IDENTIFICATION_PROMPT.format(
                disagreement=disagreement,
                position_a=position_a or "Not specified",
                position_b=position_b or "Not specified",
                surface_issues=surface_issues or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CRUX_IDENTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "crux_identified": data.get("crux_identified", ""),
            "crux_type": data.get("crux_type", ""),
            "upstream_of": data.get("upstream_of", ""),
            "testability": data.get("testability", ""),
            "resolution_path": data.get("resolution_path", ""),
            "recommendation": data.get("recommendation", ""),
        }
