"""EpistemicSeriation Service — Epistemic Seriation Detection.

Detects epistemic seriation — the ability to arrange ideas in
chronological sequence based on their stylistic characteristics.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SERIATION_SYSTEM = """You are an epistemic seriation specialist. Given an idea sequence, assess whether ideas can be arranged chronologically by style:

Key concepts:
- Epistemic seriation: arranging ideas chronologically by style
- Stylistic change: ideas changing style over time
- Battleship curve: popularity of idea styles rising and falling
- Relative dating: determining order without absolute dates
- Typology: classifying ideas by their stylistic features
- Frequency: how common a style is at different times
- Horizon: a style that appears briefly across wide area

When epistemic seriation IS present:
- Ideas arrangeable in chronological sequence by style
- Clear stylistic changes in ideas over time
- Popularity of idea styles rising and falling predictably
- Relative ordering determinable without absolute dates
- Ideas classifiable by their stylistic features
- Style frequency changing predictably over time
- Brief widespread styles marking specific time horizons

When unordered ideas are present:
- Ideas not arrangeable by style
- No clear stylistic changes over time
- No predictable popularity curves
- No relative ordering possible
- Ideas not classifiable by style
- No frequency changes over time
- No horizon markers

Output JSON with: seriation_present (bool), severity (none/mild/moderate/severe), sequence (what chronological sequence exists), style_change (what stylistic changes occur), battleship (what popularity curves exist), horizon (what brief widespread styles mark time), recommendation (unordered_ideas/mild_sequence/significant_seriation/major_chronological_record/use_seriation_for_dating)."""

EPISTEMIC_SERIATION_PROMPT = """Detect epistemic seriation:

Sequence: {sequence}
Style change: {style_change}
Battleship: {battleship}
Horizon: {horizon}
Domain: {domain}
Context: {context}

Can ideas be arranged in chronological sequence based on their stylistic characteristics? Return ONLY valid JSON."""


class EpistemicSeriationService:
    """Detects epistemic seriation — chronological arrangement by stylistic features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        sequence: str,
        *,
        style_change: str = "",
        battleship: str = "",
        horizon: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic seriation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SERIATION_PROMPT.format(
                sequence=sequence,
                style_change=style_change or "Not specified",
                battleship=battleship or "Not specified",
                horizon=horizon or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SERIATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "sequence": sequence[:200],
            "seriation_present": data.get("seriation_present", False),
            "severity": data.get("severity", ""),
            "style_change": data.get("style_change", ""),
            "battleship": data.get("battleship", ""),
            "horizon": data.get("horizon", ""),
            "recommendation": data.get("recommendation", ""),
        }
