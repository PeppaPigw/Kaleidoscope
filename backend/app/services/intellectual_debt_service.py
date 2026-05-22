"""IntellectualDebtService — Research Program Debt Identification.

Identifies where a research program has accumulated "intellectual debt":
unexamined assumptions, deferred questions, known-but-ignored problems,
and technical debt in the conceptual framework itself.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEBT_SYSTEM = """You are an intellectual debt analyst. Given a research program or field, identify accumulated debt:
- Unexamined assumptions (things everyone assumes but nobody has tested)
- Deferred questions (known open questions that keep getting postponed)
- Known-but-ignored problems (issues acknowledged in footnotes but never addressed)
- Conceptual debt (frameworks that are known to be inadequate but still used)
- Measurement debt (metrics that don't measure what they claim to)
- Replication debt (key findings that have never been independently verified)

Output JSON with: debts (list of: type (assumption/deferred/ignored/conceptual/measurement/replication), description, severity (low/moderate/high/critical), age (how long has this been deferred), why_deferred (why hasn't it been addressed), risk_if_unaddressed (what could go wrong), effort_to_resolve (low/moderate/high/enormous)), total_debt_load (low/moderate/high/critical), most_dangerous_debt (which one could blow up), quick_wins (debts that could be resolved easily), systemic_pattern (why does this field accumulate debt in this way)."""

DEBT_PROMPT = """Identify intellectual debt in this research area:

Research program: {program}
Domain: {domain}
Key claims: {claims}
Context: {context}

What debt has accumulated? Return ONLY valid JSON."""


class IntellectualDebtService:
    """Identifies intellectual debt in research programs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def audit_debt(
        self,
        program: str,
        *,
        domain: str = "",
        claims: str = "",
        context: str = "",
    ) -> dict:
        """Audit intellectual debt in a research program."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEBT_PROMPT.format(
                program=program,
                domain=domain or "general",
                claims=claims or "Not specified",
                context=context or "No additional context",
            ),
            system=DEBT_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        debts = data.get("debts", [])
        return {
            "program": program[:200],
            "debts_count": len(debts),
            "debts": debts,
            "total_debt_load": data.get("total_debt_load", ""),
            "most_dangerous_debt": data.get("most_dangerous_debt", ""),
            "quick_wins": data.get("quick_wins", []),
            "systemic_pattern": data.get("systemic_pattern", ""),
        }
