"""PrecedentFinderService — Historical Precedent Discovery.

Searches for historical precedents, analogous situations, and parallel
developments that inform current research questions. Learns from history
to predict outcomes and avoid repeated mistakes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRECEDENT_SYSTEM = """You are a historical precedent analyst. Given a current situation or research question, identify historical precedents — similar situations, parallel developments, or analogous cases from the past. For each precedent:
- How similar is it to the current situation? (structural similarity, not surface)
- What happened? (outcome)
- What can we learn? (transferable lessons)
- What's different this time? (key disanalogies that might change the outcome)

Output JSON with: precedents (list of: situation, time_period, domain, similarity_score (0-1), outcome, lessons (list), disanalogies (list), predictive_value (0-1)), strongest_precedent (which and why), pattern_across_precedents (what do they collectively suggest), predicted_outcome (based on precedent analysis), confidence (0-1), caveats (list of reasons precedents might not apply)."""

PRECEDENT_PROMPT = """Find historical precedents for this situation:

Current situation: {situation}
Domain: {domain}
Specific concern: {concern}

What historical parallels exist? What do they predict? Return ONLY valid JSON."""


class PrecedentFinderService:
    """Finds historical precedents for current research situations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_precedents(
        self,
        situation: str,
        *,
        domain: str = "",
        concern: str = "",
    ) -> dict:
        """Find historical precedents for a current situation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRECEDENT_PROMPT.format(
                situation=situation,
                domain=domain or "general",
                concern=concern or "What will happen?",
            ),
            system=PRECEDENT_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        precedents = data.get("precedents", [])
        return {
            "situation": situation[:200],
            "precedents_found": len(precedents),
            "precedents": precedents,
            "strongest": data.get("strongest_precedent", ""),
            "pattern": data.get("pattern_across_precedents", ""),
            "predicted_outcome": data.get("predicted_outcome", ""),
            "confidence": data.get("confidence", 0),
            "caveats": data.get("caveats", []),
        }
