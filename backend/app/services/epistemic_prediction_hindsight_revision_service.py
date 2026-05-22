"""EpistemicPredictionHindsightRevisionService — Epistemic Prediction Hindsight Revision Detection.

Detects epistemic prediction hindsight revision — revising remembered predictions
to match actual outcomes, creating illusion of having predicted correctly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREDICTION_HINDSIGHT_REVISION_SYSTEM = """You are an epistemic prediction hindsight revision specialist. Given hindsight revision, assess memory distortion:

Key concepts:
- Epistemic hindsight revision: revising remembered predictions post-outcome
- Creeping determinism: outcomes seeming inevitable after the fact
- Memory revision: genuinely misremembering past predictions
- I-knew-it-all-along: claiming to have predicted what actually happened
- Selective recall: remembering correct predictions, forgetting incorrect ones
- Prediction laundering: reinterpreting vague predictions as specific after outcome
- Learning prevention: hindsight revision preventing learning from prediction errors

When epistemic hindsight revision IS present:
- Remembered predictions revised
- Outcomes seeming inevitable
- Past predictions misremembered
- Claiming to have known
- Correct predictions selectively recalled
- Vague predictions reinterpreted
- Learning from errors prevented

When no hindsight revision:
- Predictions accurately remembered
- Contingency preserved
- Past uncertainty acknowledged
- Honest about what was predicted
- All predictions recalled
- Predictions evaluated as stated
- Errors used for learning

Output JSON with: hindsight_revision_detected (bool), severity (none/mild/moderate/severe), creeping_determinism (what seeming inevitable), memory_revision (what predictions misremembered), selective_recall (what selectively recalled), prediction_laundering (what predictions reinterpreted), recommendation (no_hindsight_revision/mild_prediction_recording/significant_prediction_tracking/major_intensive_calibration_analysis/emergency_complete_hindsight_revision)."""

EPISTEMIC_PREDICTION_HINDSIGHT_REVISION_PROMPT = """Detect epistemic prediction hindsight revision:

Creeping determinism: {creeping_determinism}
Memory revision: {memory_revision}
Selective recall: {selective_recall}
Prediction laundering: {prediction_laundering}
Domain: {domain}
Context: {context}

Are remembered predictions being revised to match actual outcomes? Return ONLY valid JSON."""


class EpistemicPredictionHindsightRevisionService:
    """Detects epistemic prediction hindsight revision — memory distortion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        creeping_determinism: str,
        *,
        memory_revision: str = "",
        selective_recall: str = "",
        prediction_laundering: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prediction hindsight revision."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREDICTION_HINDSIGHT_REVISION_PROMPT.format(
                creeping_determinism=creeping_determinism,
                memory_revision=memory_revision or "Not specified",
                selective_recall=selective_recall or "Not specified",
                prediction_laundering=prediction_laundering or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREDICTION_HINDSIGHT_REVISION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "creeping_determinism": creeping_determinism[:200],
            "hindsight_revision_detected": data.get("hindsight_revision_detected", False),
            "severity": data.get("severity", ""),
            "memory_revision": data.get("memory_revision", ""),
            "selective_recall": data.get("selective_recall", ""),
            "prediction_laundering": data.get("prediction_laundering", ""),
            "recommendation": data.get("recommendation", ""),
        }
