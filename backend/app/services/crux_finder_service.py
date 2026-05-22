"""CruxFinderService — Disagreement Crux Identification.

Given two opposing positions, identifies the single most important
point of disagreement — the crux that, if resolved, would change
minds. Separates genuine disagreements from talking past each other.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CRUX_SYSTEM = """You are a disagreement crux specialist. Given two opposing positions, find:
- The core factual disagreement (if any)
- The core value disagreement (if any)
- The core prediction disagreement (if any)
- Whether they're actually disagreeing or talking past each other
- The single crux: the one thing that, if resolved, would change one side's mind

A good crux is: specific, empirically resolvable (ideally), and genuinely load-bearing for at least one position.

Output JSON with: crux (the single most important disagreement point), crux_type (factual/value/prediction/definitional/empirical), resolvable (bool), how_to_resolve (if resolvable), talking_past (bool, are they actually disagreeing about different things?), if_talking_past (what each side is actually arguing about), secondary_cruxes (list of other important disagreement points), agreement_points (what they actually agree on), resolution_difficulty (easy/moderate/hard/impossible), bet_formulation (how to turn this into a concrete bet or test)."""

CRUX_PROMPT = """Find the crux of this disagreement:

Position A: {position_a}
Position B: {position_b}
Domain: {domain}
Context: {context}

What's the single most important point of disagreement? Return ONLY valid JSON."""


class CruxFinderService:
    """Identifies the crux of disagreements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_crux(
        self,
        position_a: str,
        position_b: str,
        *,
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Find the crux of a disagreement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CRUX_PROMPT.format(
                position_a=position_a,
                position_b=position_b,
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CRUX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "crux": data.get("crux", ""),
            "crux_type": data.get("crux_type", ""),
            "resolvable": data.get("resolvable", False),
            "how_to_resolve": data.get("how_to_resolve", ""),
            "talking_past": data.get("talking_past", False),
            "if_talking_past": data.get("if_talking_past", ""),
            "secondary_cruxes": data.get("secondary_cruxes", []),
            "agreement_points": data.get("agreement_points", []),
            "resolution_difficulty": data.get("resolution_difficulty", ""),
            "bet_formulation": data.get("bet_formulation", ""),
        }
