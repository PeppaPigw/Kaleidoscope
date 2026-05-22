"""CompletenessCheckerService — Research Completeness Assessment.

Given a research question and what's been investigated so far, identifies
what's still missing for a complete answer. Prevents premature conclusions
by ensuring all necessary angles have been covered.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHECK_SYSTEM = """You are a research completeness analyst. Given a research question and what's been done so far, identify what's MISSING for a complete answer. Check for:
- Uncovered perspectives: whose viewpoint hasn't been considered?
- Missing evidence types: what kinds of evidence haven't been gathered?
- Untested assumptions: what's been assumed but not verified?
- Unexplored alternatives: what competing explanations haven't been examined?
- Missing validation: what claims haven't been cross-checked?
- Scope gaps: what parts of the question haven't been addressed?

Output JSON with: completeness.overall_score (0-1, how complete is the investigation), completeness.grade (A/B/C/D/F), completeness.missing_perspectives (list), completeness.missing_evidence (list of: type, importance, how_to_get), completeness.untested_assumptions (list), completeness.unexplored_alternatives (list), completeness.validation_gaps (list), completeness.scope_gaps (list), completeness.next_steps (prioritized list of what to do next), completeness.ready_to_conclude (bool, is there enough to draw conclusions), completeness.confidence_if_concluded_now (0-1)."""

CHECK_PROMPT = """Assess research completeness:

Question: {question}
Domain: {domain}

What's been done so far:
{done_text}

What's still missing for a complete answer? Return ONLY valid JSON."""


class CompletenessCheckerService:
    """Assesses whether research is complete enough to draw conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_completeness(
        self,
        question: str,
        done: list[str],
        *,
        domain: str = "",
    ) -> dict:
        """Check how complete a research investigation is."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        done_text = "\n".join(f"- {d}" for d in done[:12]) or "Nothing yet"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHECK_PROMPT.format(
                question=question,
                domain=domain or "research",
                done_text=done_text,
            ),
            system=CHECK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        c = data.get("completeness", data)

        return {
            "question": question[:200],
            "overall_score": c.get("overall_score", 0),
            "grade": c.get("grade", ""),
            "missing_perspectives": c.get("missing_perspectives", []),
            "missing_evidence": c.get("missing_evidence", []),
            "untested_assumptions": c.get("untested_assumptions", []),
            "unexplored_alternatives": c.get("unexplored_alternatives", []),
            "validation_gaps": c.get("validation_gaps", []),
            "scope_gaps": c.get("scope_gaps", []),
            "next_steps": c.get("next_steps", []),
            "ready_to_conclude": c.get("ready_to_conclude", False),
            "confidence_if_concluded": c.get("confidence_if_concluded_now", 0),
        }
