"""InsideViewOutsideViewService — Inside View vs Outside View Detection.

Detects inside view bias — relying on personal narrative, specific
details, and causal reasoning about a particular case rather than
using reference class statistics and base rates (outside view).
Kahneman & Lovallo (1993). The inside view generates overconfident
predictions by focusing on the unique features of the case.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

INSIDE_OUTSIDE_VIEW_SYSTEM = """You are an inside/outside view specialist. Given a prediction or assessment, determine whether it relies on inside view (case-specific narrative) rather than outside view (reference class statistics):

Key concepts (Kahneman & Lovallo, 1993):
- Inside view: focusing on specific case details and causal stories
- Outside view: using reference class statistics and base rates
- Planning fallacy: inside view leads to overconfident timelines
- Reference class forecasting: what happened to similar projects?
- Narrative bias: stories are compelling but statistically unreliable
- Uniqueness bias: "this time is different" without evidence
- Base rate neglect: ignoring how things usually turn out

When inside view dominates inappropriately:
- Predictions based on "our specific situation" without reference classes
- "This project is different because..." without checking if others said the same
- Detailed causal narratives replacing statistical reasoning
- Ignoring base rates of success/failure for similar endeavors
- Overconfidence driven by understanding the specific case
- "We have a great team/plan/technology" as basis for optimistic prediction
- Failing to ask "what usually happens in cases like this?"

When inside view IS appropriate:
- Genuine unique factors that demonstrably change the reference class
- The reference class is too broad or poorly defined
- Inside knowledge reveals the case is genuinely different
- Both views are considered and the inside view is justified
- The prediction acknowledges the outside view and explains the deviation
- Specific factors have been shown to predict outcomes in this domain
- The inside view is calibrated against outside view base rates

Output JSON with: inside_view_dominant (bool), severity (none/mild/moderate/severe), prediction (what is being predicted), inside_reasoning (what case-specific reasoning is used), reference_class (what reference class would apply), base_rate (what usually happens in similar cases), uniqueness_claim (what makes this case supposedly different), recommendation (view_appropriate/mild_inside_bias/significant_inside_view_dominance/major_reference_class_neglect/consult_outside_view)."""

INSIDE_OUTSIDE_VIEW_PROMPT = """Detect inside view vs outside view:

Prediction: {prediction}
Reasoning: {reasoning}
Reference class: {reference_class}
Base rate: {base_rate}
Domain: {domain}
Context: {context}

Is this prediction relying on inside view narrative rather than outside view reference classes? Return ONLY valid JSON."""


class InsideViewOutsideViewService:
    """Detects inside view dominance over outside view."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        prediction: str,
        *,
        reasoning: str = "",
        reference_class: str = "",
        base_rate: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect inside view vs outside view."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INSIDE_OUTSIDE_VIEW_PROMPT.format(
                prediction=prediction,
                reasoning=reasoning or "Not specified",
                reference_class=reference_class or "Not specified",
                base_rate=base_rate or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=INSIDE_OUTSIDE_VIEW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "prediction": prediction[:200],
            "inside_view_dominant": data.get("inside_view_dominant", False),
            "severity": data.get("severity", ""),
            "inside_reasoning": data.get("inside_reasoning", ""),
            "reference_class": data.get("reference_class", ""),
            "base_rate": data.get("base_rate", ""),
            "uniqueness_claim": data.get("uniqueness_claim", ""),
            "recommendation": data.get("recommendation", ""),
        }
