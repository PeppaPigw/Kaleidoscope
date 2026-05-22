"""EpistemicModelReificationService — Epistemic Model Reification Detection.

Detects epistemic model reification — treating a model or analogy
as the thing itself, confusing representation with reality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MODEL_REIFICATION_SYSTEM = """You are an epistemic model reification specialist. Given models treated as reality, assess model reification:

Key concepts:
- Epistemic model reification: treating a model as the thing itself
- Representation-reality confusion: confusing the map with the territory
- Model worship: treating model outputs as ground truth
- Abstraction concretization: treating abstractions as concrete entities
- Parameter fetishism: treating model parameters as real properties
- Prediction-reality conflation: treating predictions as facts
- Framework ossification: framework becomes reality rather than lens

When epistemic model reification IS present:
- Model treated as reality
- Representation confused with thing
- Model outputs worshipped
- Abstractions concretized
- Parameters treated as real properties
- Predictions treated as facts
- Framework ossified into reality

When no model reification:
- Model understood as approximation
- Representation distinguished from reality
- Model outputs critically evaluated
- Abstractions understood as tools
- Parameters understood as constructs
- Predictions understood as estimates
- Framework understood as lens

Output JSON with: model_reification_detected (bool), severity (none/mild/moderate/severe), representation_reality_confusion (what confused), model_worship (what worshipped), abstraction_concretization (what concretized), prediction_reality_conflation (what conflated), recommendation (no_model_reification/mild_model_humility/significant_representation_awareness/major_intensive_reality_grounding/emergency_complete_model_reification)."""

EPISTEMIC_MODEL_REIFICATION_PROMPT = """Detect epistemic model reification:

Representation-reality confusion: {representation_reality_confusion}
Model worship: {model_worship}
Abstraction concretization: {abstraction_concretization}
Prediction-reality conflation: {prediction_reality_conflation}
Domain: {domain}
Context: {context}

Is a model being treated as the thing itself? Return ONLY valid JSON."""


class EpistemicModelReificationService:
    """Detects epistemic model reification — model as reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        representation_reality_confusion: str,
        *,
        model_worship: str = "",
        abstraction_concretization: str = "",
        prediction_reality_conflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic model reification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MODEL_REIFICATION_PROMPT.format(
                representation_reality_confusion=representation_reality_confusion,
                model_worship=model_worship or "Not specified",
                abstraction_concretization=abstraction_concretization or "Not specified",
                prediction_reality_conflation=prediction_reality_conflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MODEL_REIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "representation_reality_confusion": representation_reality_confusion[:200],
            "model_reification_detected": data.get("model_reification_detected", False),
            "severity": data.get("severity", ""),
            "model_worship": data.get("model_worship", ""),
            "abstraction_concretization": data.get("abstraction_concretization", ""),
            "prediction_reality_conflation": data.get("prediction_reality_conflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
