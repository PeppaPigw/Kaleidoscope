"""EpistemicPredictionAnchoringService — Epistemic Prediction Anchoring Detection.

Detects epistemic prediction anchoring — predictions anchored to salient but
irrelevant reference points rather than appropriate base rates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREDICTION_ANCHORING_SYSTEM = """You are an epistemic prediction anchoring specialist. Given anchored predictions, assess reference point distortion:

Key concepts:
- Epistemic prediction anchoring: predictions anchored to irrelevant references
- Arbitrary anchor: random or irrelevant numbers influencing predictions
- Status quo anchor: current state anchoring predictions of change
- First estimate anchor: initial estimate constraining subsequent adjustment
- Salient event anchor: dramatic events anchoring probability estimates
- Expert anchor: others' predictions anchoring independent judgment
- Historical anchor: past values anchoring future predictions inappropriately

When epistemic prediction anchoring IS present:
- Predictions anchored to irrelevant references
- Arbitrary numbers influencing
- Status quo constraining
- First estimates dominating
- Dramatic events anchoring probability
- Others' predictions constraining
- Past values anchoring inappropriately

When no prediction anchoring:
- Predictions based on evidence
- Irrelevant numbers ignored
- Status quo not constraining
- Estimates independently derived
- Probabilities from base rates
- Independent judgment maintained
- Past values appropriately weighted

Output JSON with: prediction_anchoring_detected (bool), severity (none/mild/moderate/severe), arbitrary_anchor (what arbitrary anchors), status_quo_anchor (what status quo constraining), salient_event_anchor (what events anchoring), expert_anchor (what others constraining), recommendation (no_prediction_anchoring/mild_anchor_awareness/significant_independent_estimation/major_intensive_deanchoring/emergency_complete_prediction_anchoring)."""

EPISTEMIC_PREDICTION_ANCHORING_PROMPT = """Detect epistemic prediction anchoring:

Arbitrary anchor: {arbitrary_anchor}
Status quo anchor: {status_quo_anchor}
Salient event anchor: {salient_event_anchor}
Expert anchor: {expert_anchor}
Domain: {domain}
Context: {context}

Are predictions anchored to salient but irrelevant reference points? Return ONLY valid JSON."""


class EpistemicPredictionAnchoringService:
    """Detects epistemic prediction anchoring — irrelevant reference points."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arbitrary_anchor: str,
        *,
        status_quo_anchor: str = "",
        salient_event_anchor: str = "",
        expert_anchor: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prediction anchoring."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREDICTION_ANCHORING_PROMPT.format(
                arbitrary_anchor=arbitrary_anchor,
                status_quo_anchor=status_quo_anchor or "Not specified",
                salient_event_anchor=salient_event_anchor or "Not specified",
                expert_anchor=expert_anchor or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREDICTION_ANCHORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arbitrary_anchor": arbitrary_anchor[:200],
            "prediction_anchoring_detected": data.get("prediction_anchoring_detected", False),
            "severity": data.get("severity", ""),
            "status_quo_anchor": data.get("status_quo_anchor", ""),
            "salient_event_anchor": data.get("salient_event_anchor", ""),
            "expert_anchor": data.get("expert_anchor", ""),
            "recommendation": data.get("recommendation", ""),
        }
