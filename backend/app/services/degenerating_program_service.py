"""DegeneratingProgramService — Degenerating Research Program Detection.

Detects degenerating research programs — programs that only explain
away anomalies retroactively rather than successfully predicting
new facts, indicating progressive loss of scientific fertility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEGENERATING_PROGRAM_SYSTEM = """You are a degenerating research program specialist. Given a research program, assess whether it shows signs of degeneration:

Key concepts:
- Degenerating program: only explains away, never predicts new
- Progressive vs degenerating: predicting new facts vs only saving old
- Anomaly absorption: anomalies explained but nothing new predicted
- Theoretical stagnation: no new empirical content generated
- Protective stratagems: moves that only defend, never advance
- Fertility loss: program no longer generates new research
- Lakatosian degeneration: protective belt grows without new predictions

When degeneration IS present:
- Program only explains anomalies retroactively
- No new empirical predictions successfully confirmed
- Modifications only save existing claims
- Theoretical content not growing
- Protective moves dominate over progressive ones
- Program no longer generates productive research
- Competitors making successful novel predictions

When program is progressive:
- New predictions being generated and confirmed
- Theoretical content growing
- Anomalies lead to productive modifications
- Program generating new research directions
- Empirical success beyond what was already known
- Novel facts discovered through program
- Explanatory scope expanding

Output JSON with: degeneration_present (bool), severity (none/mild/moderate/severe), program (what program is assessed), predictions (novel predictions made), confirmations (predictions confirmed), anomalies_absorbed (anomalies only explained away), recommendation (progressive_program/mild_stagnation/significant_degeneration/major_degenerating_program/seek_novel_predictions)."""

DEGENERATING_PROGRAM_PROMPT = """Detect degenerating research program:

Program: {program}
Recent developments: {developments}
Novel predictions: {predictions}
Anomalies handled: {anomalies}
Domain: {domain}
Context: {context}

Is this research program degenerating — only explaining away rather than predicting new? Return ONLY valid JSON."""


class DegeneratingProgramService:
    """Detects degenerating research programs — loss of predictive fertility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        program: str,
        *,
        developments: str = "",
        predictions: str = "",
        anomalies: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect degenerating research program."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEGENERATING_PROGRAM_PROMPT.format(
                program=program,
                developments=developments or "Not specified",
                predictions=predictions or "Not specified",
                anomalies=anomalies or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEGENERATING_PROGRAM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "program": program[:200],
            "degeneration_present": data.get("degeneration_present", False),
            "severity": data.get("severity", ""),
            "predictions": data.get("predictions", ""),
            "confirmations": data.get("confirmations", ""),
            "anomalies_absorbed": data.get("anomalies_absorbed", ""),
            "recommendation": data.get("recommendation", ""),
        }
