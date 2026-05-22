"""SynthesisArbitratorService — Multi-Engine Conflict Resolution.

When multiple research engines produce conflicting conclusions, this
service arbitrates: weighs evidence quality, identifies why disagreement
exists, and produces a reasoned verdict with explicit uncertainty bounds.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARBITRATE_SYSTEM = """You are a synthesis arbitrator. Multiple research analyses have produced conflicting conclusions. Your job is to:
1. Identify the exact points of disagreement
2. Assess why each analysis reached its conclusion
3. Weigh the evidence quality behind each position
4. Determine if the conflict is real or apparent (different framings of compatible truths)
5. Produce a reasoned verdict

Output JSON with: conflict_analysis.disagreement_points (list of: point, position_a, position_b, nature (factual/interpretive/methodological/framing)), conflict_analysis.root_causes (list of why they disagree), conflict_analysis.evidence_weights (which position has stronger evidence and why), conflict_analysis.verdict (which position is better supported), conflict_analysis.confidence (0-1), conflict_analysis.residual_uncertainty (what remains unresolved), conflict_analysis.reconciliation (can both be partially right? how?), conflict_analysis.recommendation (what to do next)."""

ARBITRATE_PROMPT = """Arbitrate between these conflicting research conclusions:

Question: {question}

Position A ({source_a}):
{conclusion_a}

Position B ({source_b}):
{conclusion_b}

Additional context:
{context}

Which position is better supported? Can they be reconciled? Return ONLY valid JSON."""


class SynthesisArbitratorService:
    """Arbitrates between conflicting research conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def arbitrate(
        self,
        question: str,
        conclusion_a: str,
        conclusion_b: str,
        *,
        source_a: str = "Analysis A",
        source_b: str = "Analysis B",
        context: str = "",
        domain: str = "",
    ) -> dict:
        """Arbitrate between two conflicting conclusions."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARBITRATE_PROMPT.format(
                question=question,
                source_a=source_a,
                source_b=source_b,
                conclusion_a=conclusion_a,
                conclusion_b=conclusion_b,
                context=context or "No additional context",
            ),
            system=ARBITRATE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        analysis = data.get("conflict_analysis", data)

        return {
            "question": question,
            "disagreement_points": analysis.get("disagreement_points", []),
            "root_causes": analysis.get("root_causes", []),
            "evidence_weights": analysis.get("evidence_weights", ""),
            "verdict": analysis.get("verdict", ""),
            "confidence": analysis.get("confidence", 0),
            "residual_uncertainty": analysis.get("residual_uncertainty", ""),
            "reconciliation": analysis.get("reconciliation", ""),
            "recommendation": analysis.get("recommendation", ""),
        }
