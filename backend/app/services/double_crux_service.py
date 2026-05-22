"""DoubleCruxService — Double Crux Detection.

Detects when disagreements have a shared crux — a single underlying
belief that, if resolved, would resolve the surface disagreement for
both parties. CFAR technique for productive disagreement resolution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DOUBLE_CRUX_SYSTEM = """You are a double crux specialist. Given a disagreement, assess whether there is a shared crux — an underlying belief that would resolve the disagreement for both parties if settled:

Key concepts (CFAR):
- Double crux: a belief that is crux for BOTH parties
- Crux: a belief that, if changed, would change your conclusion
- Operationalization: making the crux testable
- Productive disagreement: finding what would actually change minds
- Belief dependency: which beliefs depend on which
- Factual vs value disagreement: cruxes work for factual disputes
- Resolution path: how to test or settle the crux

When a double crux EXISTS:
- Both parties can identify a specific belief that drives their conclusion
- The same belief is load-bearing for both sides (in opposite directions)
- Settling this belief would genuinely change both parties' positions
- The crux is more concrete/testable than the surface disagreement
- The disagreement has a factual component that could be resolved
- Both parties agree that the crux is relevant to their position
- Evidence or argument could in principle settle the crux

When no double crux exists:
- The disagreement is fundamentally about values, not facts
- Each party's crux is different (no shared crux)
- Neither party can identify what would change their mind
- The positions are held for identity reasons, not epistemic ones
- The disagreement is about definitions, not substance
- Multiple independent reasons support each position (no single crux)
- The parties are not genuinely trying to resolve the disagreement

Output JSON with: double_crux_found (bool), severity (none/mild/moderate/severe), disagreement (what is disagreed about), crux_candidate (what might be the shared crux), party_a_dependency (how A's position depends on crux), party_b_dependency (how B's position depends on crux), testability (can the crux be tested), recommendation (crux_identified/possible_crux/no_shared_crux/value_disagreement/operationalize_and_test_crux)."""

DOUBLE_CRUX_PROMPT = """Detect double crux:

Disagreement: {disagreement}
Party A's position: {party_a}
Party B's position: {party_b}
What would change minds: {mind_change}
Domain: {domain}
Context: {context}

Is there a shared crux — an underlying belief that would resolve this disagreement for both parties? Return ONLY valid JSON."""


class DoubleCruxService:
    """Detects double cruxes — shared underlying beliefs that could resolve disagreements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        party_a: str = "",
        party_b: str = "",
        mind_change: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect double crux."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DOUBLE_CRUX_PROMPT.format(
                disagreement=disagreement,
                party_a=party_a or "Not specified",
                party_b=party_b or "Not specified",
                mind_change=mind_change or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DOUBLE_CRUX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "double_crux_found": data.get("double_crux_found", False),
            "severity": data.get("severity", ""),
            "crux_candidate": data.get("crux_candidate", ""),
            "party_a_dependency": data.get("party_a_dependency", ""),
            "party_b_dependency": data.get("party_b_dependency", ""),
            "testability": data.get("testability", ""),
            "recommendation": data.get("recommendation", ""),
        }
