"""EpistemicStemCellService — Epistemic Stem Cell Detection.

Detects epistemic stem cell — undifferentiated ideas capable of becoming
anything, maintaining pluripotency until triggered to specialize.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STEM_CELL_SYSTEM = """You are an epistemic stem cell specialist. Given intellectual ideas, assess whether undifferentiated ideas maintain pluripotency:

Key concepts:
- Epistemic stem cell: undifferentiated ideas capable of becoming anything
- Pluripotency: ability to become many different types
- Self-renewal: maintaining the undifferentiated state
- Niche: environment maintaining stemness
- Asymmetric division: producing one stem and one specialized
- Reprogramming: returning specialized ideas to stem state
- Quiescence: dormant state preserving potential

When epistemic stem cell IS present:
- Undifferentiated ideas capable of becoming anything
- Ability to develop into many different intellectual types
- Maintaining the undifferentiated state through self-renewal
- Specific environment maintaining the stem state
- Producing both stem and specialized ideas
- Possibility of returning specialized ideas to stem state
- Dormant ideas preserving future potential

When fully committed is present:
- All ideas already specialized
- No ability to become other types
- No self-renewal of undifferentiated state
- No stemness-maintaining environment
- Only producing specialized ideas
- No reprogramming possible
- No dormant potential

Output JSON with: stem_cell_present (bool), severity (none/mild/moderate/severe), pluripotency (what becoming-anything ability), self_renewal (what state maintenance), niche (what maintaining environment), reprogramming (what return to stem state), recommendation (fully_committed/mild_stemness/significant_stem_cell/major_pluripotency/protect_stem_cell_niche)."""

EPISTEMIC_STEM_CELL_PROMPT = """Detect epistemic stem cell:

Pluripotency: {pluripotency}
Self-renewal: {self_renewal}
Niche: {niche}
Reprogramming: {reprogramming}
Domain: {domain}
Context: {context}

Are undifferentiated ideas maintaining pluripotency, capable of becoming anything until triggered to specialize? Return ONLY valid JSON."""


class EpistemicStemCellService:
    """Detects epistemic stem cell — undifferentiated ideas capable of becoming anything."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pluripotency: str,
        *,
        self_renewal: str = "",
        niche: str = "",
        reprogramming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stem cell."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STEM_CELL_PROMPT.format(
                pluripotency=pluripotency,
                self_renewal=self_renewal or "Not specified",
                niche=niche or "Not specified",
                reprogramming=reprogramming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STEM_CELL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pluripotency": pluripotency[:200],
            "stem_cell_present": data.get("stem_cell_present", False),
            "severity": data.get("severity", ""),
            "self_renewal": data.get("self_renewal", ""),
            "niche": data.get("niche", ""),
            "reprogramming": data.get("reprogramming", ""),
            "recommendation": data.get("recommendation", ""),
        }
