"""PredictionGeneratorService — Predictive Consequence Derivation.

Given a claim or theory, derives testable predictions that should follow
if the claim is true. Identifies what we should observe, what would be
surprising, and what observations would update our confidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PREDICT_SYSTEM = """You are a prediction derivation specialist. Given a claim or theory, derive concrete testable predictions. Good predictions:
- Follow logically from the claim
- Are specific enough to be checked
- Have clear timelines or conditions
- Distinguish this theory from alternatives
- Range from near-certain to surprising-if-true

For each prediction, assess:
- How confident we should be IF the claim is true
- Whether the prediction is unique to this theory or shared with alternatives
- How easy it is to check
- What finding it false would mean for the claim

Output JSON with: predictions (list of: prediction, confidence_if_true (0-1), uniqueness (unique/shared/common), testability (easy/moderate/hard/impossible), timeline (immediate/short_term/long_term/indefinite), if_false_means (what it means for the claim if this prediction fails)), strongest_test (which prediction best distinguishes this theory), prediction_cluster (groups of related predictions), overall_testability (0-1, how testable is this theory overall), degreeOfFreedom (how many ways could the theory wiggle out of failed predictions)."""

PREDICT_PROMPT = """Derive testable predictions from this claim:

Claim: {claim}
Domain: {domain}
Context: {context}
Timeframe: {timeframe}

What should we observe if this is true? Return ONLY valid JSON."""


class PredictionGeneratorService:
    """Derives testable predictions from claims and theories."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict(
        self,
        claim: str,
        *,
        domain: str = "",
        context: str = "",
        timeframe: str = "",
    ) -> dict:
        """Generate testable predictions from a claim."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PREDICT_PROMPT.format(
                claim=claim,
                domain=domain or "general",
                context=context or "No additional context",
                timeframe=timeframe or "Any timeframe",
            ),
            system=PREDICT_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        predictions = data.get("predictions", [])
        return {
            "claim": claim[:200],
            "predictions_count": len(predictions),
            "predictions": predictions,
            "strongest_test": data.get("strongest_test", ""),
            "prediction_clusters": data.get("prediction_cluster", []),
            "overall_testability": data.get("overall_testability", 0),
            "degree_of_freedom": data.get("degreeOfFreedom", ""),
        }
