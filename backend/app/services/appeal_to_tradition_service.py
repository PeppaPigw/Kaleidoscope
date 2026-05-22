"""AppealToTraditionService — Appeal to Tradition Detection.

Detects appeal to tradition (argumentum ad antiquitatem) — arguing
that something is good, correct, or preferable because it is
traditional or has always been done that way.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_TRADITION_SYSTEM = """You are an appeal to tradition specialist. Given an argument, assess whether it fallaciously equates 'traditional' or 'long-standing' with 'correct' or 'good':

Key concepts:
- Argumentum ad antiquitatem: old = good fallacy
- Conservative bias: preferring existing practices without justification
- Lindy effect: sometimes longevity IS evidence of fitness (distinguish)
- Chesterton's fence: understanding WHY a tradition exists before removing it
- Path dependence: traditions may persist due to switching costs, not merit
- Survivorship of practices: some traditions survive for good reasons
- Cultural inertia: practices continuing from habit, not evaluation

When appeal to tradition IS present:
- "We've always done it this way, so it must be right"
- Using age of practice as sole justification
- "This is how our ancestors did it" as proof of correctness
- Rejecting change solely because it departs from tradition
- Treating historical practice as self-justifying
- "If it ain't broke don't fix it" when it IS broken but familiar
- Conflating familiarity with optimality

When appeal to tradition is NOT present:
- Tradition cited alongside independent reasons for its value
- Chesterton's fence reasoning (understanding the tradition's purpose)
- Lindy effect applied appropriately (time-tested = robust)
- Acknowledging tradition while evaluating on merits
- Historical evidence of effectiveness (empirical, not just old)
- Tradition as one factor among many in decision-making
- Noting that a practice has survived competitive pressure

Output JSON with: appeal_to_tradition_present (bool), severity (none/mild/moderate/severe), claim (what is argued), tradition_cited (what tradition is invoked), independent_merit (does the tradition have independent justification), alternatives_considered (were alternatives evaluated), recommendation (no_appeal_to_tradition/mild_conservatism/significant_appeal_to_tradition/major_tradition_worship/evaluate_on_merits)."""

APPEAL_TRADITION_PROMPT = """Detect appeal to tradition:

Argument: {argument}
Tradition cited: {tradition}
Independent justification: {justification}
Alternatives considered: {alternatives}
Domain: {domain}
Context: {context}

Does this argue something is good merely because it's traditional? Return ONLY valid JSON."""


class AppealToTraditionService:
    """Detects appeal to tradition — equating old/traditional with good."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        tradition: str = "",
        justification: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to tradition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_TRADITION_PROMPT.format(
                argument=argument,
                tradition=tradition or "Not specified",
                justification=justification or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_TRADITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_tradition_present": data.get("appeal_to_tradition_present", False),
            "severity": data.get("severity", ""),
            "tradition_cited": data.get("tradition_cited", ""),
            "independent_merit": data.get("independent_merit", ""),
            "alternatives_considered": data.get("alternatives_considered", ""),
            "recommendation": data.get("recommendation", ""),
        }
