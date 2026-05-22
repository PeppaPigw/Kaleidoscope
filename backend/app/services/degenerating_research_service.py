"""DegeneratingResearchService — Degenerating Research Program Detection.

Detects degenerating research programs — programs that only explain
retroactively and never predict novel facts, indicating they are
losing empirical content over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEGENERATING_RESEARCH_SYSTEM = """You are a research program evaluation specialist. Given a research program or theory, assess whether it is degenerating in the Lakatosian sense:

Key concepts:
- Progressive program: predicts novel facts, some confirmed
- Degenerating program: only explains retroactively, never predicts
- Novel prediction: prediction made before observation
- Protective belt: auxiliary hypotheses shielding hard core
- Hard core: unfalsifiable central commitments of program
- Empirical content: set of potential falsifiers
- Problem shift: progressive (gains content) vs degenerating (loses content)

When degeneration IS present:
- Theory only explains after the fact, never predicts
- Each modification reduces testability
- No novel predictions confirmed
- Protective belt growing without empirical gains
- Competitors making successful predictions in same domain
- Research program stagnant — no new empirical content
- Explanations becoming increasingly convoluted

When program is progressive:
- Novel predictions being made and tested
- Some novel predictions confirmed
- Empirical content growing over time
- Modifications lead to new testable implications
- Program generating new research questions
- Explanatory scope expanding
- Simplicity maintained or improved

Output JSON with: degenerating (bool), severity (none/mild/moderate/severe), program (what research program), novel_predictions (what predictions it makes), retroactive_only (what it only explains after the fact), competitor_success (whether competitors predict better), recommendation (progressive_program/mild_stagnation/significant_degeneration/major_degenerating/consider_alternatives)."""

DEGENERATING_RESEARCH_PROMPT = """Detect degenerating research program:

Program: {program}
Claims: {claims}
Predictions: {predictions}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is this research program degenerating — only explaining retroactively, never predicting? Return ONLY valid JSON."""


class DegeneratingResearchService:
    """Detects degenerating research programs — retroactive-only explanation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        program: str,
        *,
        claims: str = "",
        predictions: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect degenerating research program."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEGENERATING_RESEARCH_PROMPT.format(
                program=program,
                claims=claims or "Not specified",
                predictions=predictions or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEGENERATING_RESEARCH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "program": program[:200],
            "degenerating": data.get("degenerating", False),
            "severity": data.get("severity", ""),
            "novel_predictions": data.get("novel_predictions", ""),
            "retroactive_only": data.get("retroactive_only", ""),
            "competitor_success": data.get("competitor_success", ""),
            "recommendation": data.get("recommendation", ""),
        }
