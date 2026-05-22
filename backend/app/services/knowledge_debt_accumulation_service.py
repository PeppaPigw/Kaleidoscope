"""KnowledgeDebtService — Knowledge Debt Accumulation Detection.

Detects knowledge debt accumulation — the buildup of unresolved
questions, untested assumptions, and deferred investigations that
compound over time, creating systemic epistemic risk.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_DEBT_ACCUMULATION_SYSTEM = """You are a knowledge debt accumulation specialist. Given a knowledge system, assess whether dangerous knowledge debt is accumulating:

Key concepts:
- Knowledge debt: unresolved questions accumulating
- Assumption debt: untested assumptions compounding
- Investigation deferral: questions postponed indefinitely
- Epistemic technical debt: shortcuts creating future risk
- Compounding ignorance: unknowns building on unknowns
- Deferred validation: claims accepted without verification
- Systemic epistemic risk: accumulated uncertainty

When knowledge debt accumulation IS present:
- Unresolved questions accumulating without plan
- Untested assumptions compounding over time
- Investigations deferred indefinitely
- Epistemic shortcuts creating future risk
- Unknowns building on other unknowns
- Claims accepted without planned verification
- Accumulated uncertainty creating systemic risk

When knowledge prioritization is appropriate:
- Questions prioritized by importance
- Assumptions tracked and scheduled for testing
- Deferrals conscious and time-bounded
- Shortcuts acknowledged with payback plan
- Dependencies between unknowns mapped
- Verification scheduled proportionally
- Risk managed through awareness

Output JSON with: debt_present (bool), severity (none/mild/moderate/severe), system (what system carries debt), debt_type (what kind of debt), accumulation (how debt accumulates), risk (what risk results), recommendation (appropriate_knowledge_prioritization/mild_question_backlog/significant_knowledge_debt/major_epistemic_risk/address_knowledge_debt)."""

KNOWLEDGE_DEBT_ACCUMULATION_PROMPT = """Detect knowledge debt accumulation:

System: {system}
Unresolved questions: {questions}
Untested assumptions: {assumptions}
Deferral pattern: {deferral}
Domain: {domain}
Context: {context}

Is dangerous knowledge debt accumulating and creating systemic epistemic risk? Return ONLY valid JSON."""


class KnowledgeDebtService:
    """Detects knowledge debt accumulation — compounding epistemic risk."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        questions: str = "",
        assumptions: str = "",
        deferral: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge debt accumulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_DEBT_ACCUMULATION_PROMPT.format(
                system=system,
                questions=questions or "Not specified",
                assumptions=assumptions or "Not specified",
                deferral=deferral or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_DEBT_ACCUMULATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "debt_present": data.get("debt_present", False),
            "severity": data.get("severity", ""),
            "debt_type": data.get("debt_type", ""),
            "accumulation": data.get("accumulation", ""),
            "risk": data.get("risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
