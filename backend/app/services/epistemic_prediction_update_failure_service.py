"""EpistemicPredictionUpdateFailureService — Epistemic Prediction Update Failure Detection.

Detects epistemic prediction update failure — failing to update predictions
appropriately when new evidence arrives, maintaining stale forecasts.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREDICTION_UPDATE_FAILURE_SYSTEM = """You are an epistemic prediction update failure specialist. Given update failures, assess evidence integration distortion:

Key concepts:
- Epistemic prediction update failure: not updating predictions with new evidence
- Conservatism bias: insufficient updating from prior beliefs
- Evidence discounting: new evidence discounted to maintain prediction
- Commitment escalation: doubling down on failed predictions
- Sunk cost prediction: maintaining prediction because of past investment
- Cognitive inertia: predictions persisting despite contradicting evidence
- Selective updating: updating only when evidence confirms prediction

When epistemic prediction update failure IS present:
- Predictions not updated with evidence
- Insufficient updating from priors
- New evidence discounted
- Failed predictions doubled down on
- Past investment maintaining prediction
- Predictions persisting despite contradiction
- Only confirming evidence updating

When no update failure:
- Predictions updated with evidence
- Appropriate Bayesian updating
- New evidence incorporated
- Failed predictions revised
- Sunk costs not influencing
- Contradicting evidence integrated
- All evidence updating symmetrically

Output JSON with: update_failure_detected (bool), severity (none/mild/moderate/severe), conservatism_bias (what insufficient updating), evidence_discounting (what evidence discounted), commitment_escalation (what predictions doubled down), selective_updating (what selective updating), recommendation (no_update_failure/mild_evidence_integration/significant_bayesian_updating/major_intensive_prediction_revision/emergency_complete_update_failure)."""

EPISTEMIC_PREDICTION_UPDATE_FAILURE_PROMPT = """Detect epistemic prediction update failure:

Conservatism bias: {conservatism_bias}
Evidence discounting: {evidence_discounting}
Commitment escalation: {commitment_escalation}
Selective updating: {selective_updating}
Domain: {domain}
Context: {context}

Are predictions failing to update when new evidence arrives? Return ONLY valid JSON."""


class EpistemicPredictionUpdateFailureService:
    """Detects epistemic prediction update failure — stale forecasts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conservatism_bias: str,
        *,
        evidence_discounting: str = "",
        commitment_escalation: str = "",
        selective_updating: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prediction update failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREDICTION_UPDATE_FAILURE_PROMPT.format(
                conservatism_bias=conservatism_bias,
                evidence_discounting=evidence_discounting or "Not specified",
                commitment_escalation=commitment_escalation or "Not specified",
                selective_updating=selective_updating or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREDICTION_UPDATE_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conservatism_bias": conservatism_bias[:200],
            "update_failure_detected": data.get("update_failure_detected", False),
            "severity": data.get("severity", ""),
            "evidence_discounting": data.get("evidence_discounting", ""),
            "commitment_escalation": data.get("commitment_escalation", ""),
            "selective_updating": data.get("selective_updating", ""),
            "recommendation": data.get("recommendation", ""),
        }
