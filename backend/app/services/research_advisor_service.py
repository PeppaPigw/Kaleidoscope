"""ResearchAdvisorService — Next-Best-Action Recommender.

Given the current state of a research investigation (what's known, what's
uncertain, what's been tried), recommends the single most valuable next
action. Acts as the strategic advisor that prevents wasted effort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ADVISE_SYSTEM = """You are a research strategy advisor. Given the current state of an investigation, recommend the single most valuable next action. Consider:
- Information value: what would reduce uncertainty the most?
- Effort efficiency: what gives the best insight-per-hour?
- Dependency ordering: what unblocks the most downstream work?
- Diminishing returns: what areas have been over-investigated?
- Surprise potential: where might we find something unexpected?

Output JSON with: advice.current_state_assessment (1-2 sentences), advice.recommended_action (specific, actionable next step), advice.tool_to_use (which Kaleidoscope tool to invoke), advice.tool_arguments (suggested arguments for that tool), advice.rationale (why this is the highest-value action), advice.expected_information_gain (what we'll learn), advice.alternatives (list of alternative/value/why_not_first), advice.stop_condition (when to stop investigating this direction), advice.confidence (0-1)."""

ADVISE_PROMPT = """Advise on next research action:

Research question: {question}
Domain: {domain}

What we know so far:
{known_text}

What's uncertain:
{uncertain_text}

What's been tried:
{tried_text}

What is the single most valuable next action? Return ONLY valid JSON."""


class ResearchAdvisorService:
    """Recommends the most valuable next research action."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def advise_next(
        self,
        question: str,
        *,
        domain: str = "",
        known: list[str] | None = None,
        uncertain: list[str] | None = None,
        tried: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Recommend the single most valuable next research action."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(question, dossier_id)
        all_known = (known or []) + extra
        known_text = "\n".join(f"- {k}" for k in all_known[:8]) or "Starting fresh"
        uncertain_text = "\n".join(f"- {u}" for u in (uncertain or [])[:6]) or "Everything"
        tried_text = "\n".join(f"- {t}" for t in (tried or [])[:6]) or "Nothing yet"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ADVISE_PROMPT.format(
                question=question,
                domain=domain or "research",
                known_text=known_text,
                uncertain_text=uncertain_text,
                tried_text=tried_text,
            ),
            system=ADVISE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        advice = data.get("advice", data)

        return {
            "question": question,
            "state_assessment": advice.get("current_state_assessment", ""),
            "recommended_action": advice.get("recommended_action", ""),
            "tool_to_use": advice.get("tool_to_use", ""),
            "tool_arguments": advice.get("tool_arguments", {}),
            "rationale": advice.get("rationale", ""),
            "expected_gain": advice.get("expected_information_gain", ""),
            "alternatives": advice.get("alternatives", []),
            "stop_condition": advice.get("stop_condition", ""),
            "confidence": advice.get("confidence", 0),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
