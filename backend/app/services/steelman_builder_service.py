"""SteelmanBuilderService — Strongest Argument Construction.

Before critiquing a position, constructs the strongest possible version
of it (steelmanning). Ensures fair evaluation by giving every position
its best shot before assessing weaknesses.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STEELMAN_SYSTEM = """You are a steelman construction specialist. Given a position or argument (possibly stated weakly or with obvious flaws), construct the STRONGEST possible version of it. This means:
- Fix logical errors while preserving the core claim
- Add the best available evidence
- Use the most charitable interpretation
- Address obvious objections preemptively
- Frame it in the most compelling way possible

Then assess: even at its strongest, how good is this argument?

Output JSON with: steelman.original_position (as stated), steelman.strongest_version (the steelmanned argument), steelman.improvements_made (list of what you fixed/strengthened), steelman.best_evidence (strongest evidence for this position), steelman.preemptive_rebuttals (how it handles obvious objections), steelman.remaining_weaknesses (even at its best, what's still weak), steelman.overall_strength (0-1, how strong is the steelmanned version), steelman.verdict (strong/moderate/weak_even_steelmanned), steelman.fair_confidence (what confidence should someone have in this position)."""

STEELMAN_PROMPT = """Steelman this position:

Position: {position}
Domain: {domain}
Context: {context}

Build the STRONGEST possible version of this argument. Return ONLY valid JSON."""


class SteelmanBuilderService:
    """Constructs the strongest version of arguments for fair evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def steelman(
        self,
        position: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Build the strongest version of a position."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STEELMAN_PROMPT.format(
                position=position,
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STEELMAN_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        sm = data.get("steelman", data)

        return {
            "original": sm.get("original_position", position[:200]),
            "strongest_version": sm.get("strongest_version", ""),
            "improvements": sm.get("improvements_made", []),
            "best_evidence": sm.get("best_evidence", ""),
            "preemptive_rebuttals": sm.get("preemptive_rebuttals", []),
            "remaining_weaknesses": sm.get("remaining_weaknesses", []),
            "overall_strength": sm.get("overall_strength", 0),
            "verdict": sm.get("verdict", ""),
            "fair_confidence": sm.get("fair_confidence", 0),
        }
