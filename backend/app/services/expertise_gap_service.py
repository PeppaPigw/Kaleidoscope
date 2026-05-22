"""ExpertiseGapService — Missing Expertise & Blind Spot Identification.

Identifies what expertise is missing from a research team or analysis,
what blind spots that creates, and what disciplines should be consulted
to fill the gaps.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPERTISE_GAP_SYSTEM = """You are an expertise gap analyst. Given a research question and the expertise available, identify:
- What expertise is present and what's missing
- What blind spots the missing expertise creates
- What disciplines should be consulted
- Whether the missing expertise could change the conclusion
- What questions the team can't even formulate without the missing expertise

Output JSON with: available_expertise (list), missing_expertise (list of: discipline, why_needed, blind_spot_created, impact_on_conclusion (low/moderate/high/critical)), critical_gaps (expertise whose absence could invalidate the work), recommended_consultations (list of: discipline, specific_question_to_ask), unknown_unknowns_risk (0-1, how likely are there questions they can't even formulate), interdisciplinary_bridges (connections between fields that would help), overall_coverage (0-1, how well-covered is the question)."""

EXPERTISE_GAP_PROMPT = """Identify expertise gaps:

Research question: {question}
Available expertise: {expertise}
Domain: {domain}
Current approach: {approach}

What expertise is missing? Return ONLY valid JSON."""


class ExpertiseGapService:
    """Identifies missing expertise and resulting blind spots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_gaps(
        self,
        question: str,
        expertise: list[str],
        *,
        domain: str = "",
        approach: str = "",
    ) -> dict:
        """Find expertise gaps for a research question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        expertise_formatted = ", ".join(expertise[:10])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPERTISE_GAP_PROMPT.format(
                question=question,
                expertise=expertise_formatted or "Not specified",
                domain=domain or "general",
                approach=approach or "Not specified",
            ),
            system=EXPERTISE_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        missing = data.get("missing_expertise", [])
        return {
            "question": question[:200],
            "available_expertise": data.get("available_expertise", expertise),
            "missing_count": len(missing),
            "missing_expertise": missing,
            "critical_gaps": data.get("critical_gaps", []),
            "recommended_consultations": data.get("recommended_consultations", []),
            "unknown_unknowns_risk": data.get("unknown_unknowns_risk", 0),
            "interdisciplinary_bridges": data.get("interdisciplinary_bridges", []),
            "overall_coverage": data.get("overall_coverage", 0),
        }
