"""KnowledgeDebtService — Knowledge Debt Detection.

Detects knowledge debt — accumulated unverified assumptions,
untested beliefs, and unexamined premises creating fragile
knowledge structures that may collapse under scrutiny.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_DEBT_SYSTEM = """You are a knowledge debt specialist. Given a knowledge structure, assess whether unverified assumptions have accumulated dangerously:

Key concepts:
- Knowledge debt: unverified assumptions accumulating over time
- Assumption chains: conclusions built on unverified premises
- Verification deficit: gap between claims made and claims tested
- Fragile knowledge: structures that collapse when assumptions fail
- Technical debt analogy: shortcuts that compound over time
- Epistemic maintenance: ongoing verification and updating
- Foundation risk: unexamined premises supporting large structures

When knowledge debt IS present:
- Many assumptions taken on faith without verification
- Conclusions built on long chains of unverified premises
- No systematic verification of foundational claims
- Knowledge structure would collapse if key assumptions fail
- Assumptions from different eras mixed without updating
- No maintenance or review of foundational beliefs
- Increasing distance between claims and evidence

When knowledge is well-maintained:
- Key assumptions regularly verified
- Foundational premises tested and updated
- Verification proportional to importance
- Assumption chains kept short
- Regular epistemic maintenance performed
- Fragile dependencies identified and strengthened
- Knowledge debt tracked and managed

Output JSON with: debt_present (bool), severity (none/mild/moderate/severe), structure (what knowledge structure), unverified_assumptions (what assumptions lack verification), chain_length (how long assumption chains are), fragility (what would collapse if assumptions fail), recommendation (well_maintained/mild_debt/significant_accumulation/major_fragility/verify_foundations)."""

KNOWLEDGE_DEBT_PROMPT = """Detect knowledge debt:

Structure: {structure}
Key assumptions: {assumptions}
Verification history: {verification}
Dependencies: {dependencies}
Domain: {domain}
Context: {context}

Has knowledge debt accumulated dangerously in this structure? Return ONLY valid JSON."""


class KnowledgeDebtService:
    """Detects knowledge debt — accumulated unverified assumptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        assumptions: str = "",
        verification: str = "",
        dependencies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge debt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_DEBT_PROMPT.format(
                structure=structure,
                assumptions=assumptions or "Not specified",
                verification=verification or "Not specified",
                dependencies=dependencies or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_DEBT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "debt_present": data.get("debt_present", False),
            "severity": data.get("severity", ""),
            "unverified_assumptions": data.get("unverified_assumptions", ""),
            "chain_length": data.get("chain_length", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
