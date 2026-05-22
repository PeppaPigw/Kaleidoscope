"""ReferenceClassForecastingService — Reference Class Forecasting Detection.

Detects failure to use reference class forecasting — making predictions
without consulting what happened in similar past cases. Flyvbjerg (2006).
Instead of asking "what usually happens when people try X?", the
predictor relies on case-specific reasoning that typically produces
overconfident estimates.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REFERENCE_CLASS_SYSTEM = """You are a reference class forecasting specialist. Given a prediction, assess whether appropriate reference classes are being consulted:

Key concepts (Flyvbjerg, 2006):
- Reference class forecasting: using outcomes of similar past cases
- Planning fallacy: systematic underestimation without reference classes
- Base rate: how often does this type of thing succeed/fail?
- Similarity judgment: what counts as a "similar" case?
- Optimism bias: inside view produces systematically optimistic predictions
- Anchoring on plans: using the plan as the prediction rather than outcomes
- Distribution of outcomes: what's the range, not just the expected value?

When reference class neglect IS present:
- Predictions made without consulting similar past cases
- "Our project will take 6 months" without checking how long similar projects took
- Optimistic estimates based on plans rather than outcomes
- No mention of base rates or historical precedent
- Uniqueness claims without evidence of genuine uniqueness
- Confidence intervals that are too narrow for the domain
- Ignoring the distribution of outcomes for similar endeavors

When case-specific prediction IS appropriate:
- Reference classes have been consulted and the deviation is justified
- Genuine unique factors have been identified and validated
- The prediction acknowledges the reference class and explains the difference
- Historical data is genuinely unavailable or inapplicable
- The predictor has a track record of accurate case-specific predictions
- Both reference class and case-specific factors are weighed
- Uncertainty is calibrated to the reference class distribution

Output JSON with: reference_class_neglect_present (bool), severity (none/mild/moderate/severe), prediction (what is being predicted), reference_class (what reference class would apply), base_rate (what the reference class suggests), deviation (how far is the prediction from the base rate), justification (is the deviation justified), recommendation (reference_class_consulted/mild_neglect/significant_reference_class_failure/major_planning_fallacy/consult_reference_class)."""

REFERENCE_CLASS_PROMPT = """Detect reference class forecasting failure:

Prediction: {prediction}
Method: {method}
Reference class: {reference_class}
Historical: {historical}
Domain: {domain}
Context: {context}

Is this prediction being made without consulting appropriate reference classes? Return ONLY valid JSON."""


class ReferenceClassForecastingService:
    """Detects failure to use reference class forecasting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        method: str = "",
        reference_class: str = "",
        historical: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reference class forecasting failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REFERENCE_CLASS_PROMPT.format(
                prediction=prediction,
                method=method or "Not specified",
                reference_class=reference_class or "Not specified",
                historical=historical or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REFERENCE_CLASS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "reference_class_neglect_present": data.get("reference_class_neglect_present", False),
            "severity": data.get("severity", ""),
            "reference_class": data.get("reference_class", ""),
            "base_rate": data.get("base_rate", ""),
            "deviation": data.get("deviation", ""),
            "justification": data.get("justification", ""),
            "recommendation": data.get("recommendation", ""),
        }
