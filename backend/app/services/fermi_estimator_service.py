"""FermiEstimatorService — Order-of-Magnitude Estimation.

Takes a question that seems impossible to answer precisely and breaks
it into estimable components to produce a rough order-of-magnitude
answer with explicit uncertainty bounds.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FERMI_SYSTEM = """You are a Fermi estimation specialist. Given a hard-to-answer question, break it into estimable components:
- Decompose into factors you can estimate independently
- For each factor, give a point estimate and a range (low/high)
- Multiply/combine to get the final estimate
- Propagate uncertainty to give confidence bounds
- Flag which factors you're least sure about

Output JSON with: decomposition (list of: factor, reasoning, point_estimate, low_estimate, high_estimate, unit, confidence (0-1)), calculation (how factors combine), point_estimate (final answer), low_bound (pessimistic), high_bound (optimistic), unit (of the final answer), order_of_magnitude (e.g. "tens of thousands"), most_uncertain_factor (which factor dominates the uncertainty), sanity_checks (ways to verify the estimate is reasonable), known_reference_points (similar quantities that are known)."""

FERMI_PROMPT = """Estimate this quantity:

Question: {question}
Domain: {domain}
Context: {context}
Precision needed: {precision}

Break it down and estimate. Return ONLY valid JSON."""


class FermiEstimatorService:
    """Produces order-of-magnitude estimates for hard questions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def estimate(
        self,
        question: str,
        *,
        domain: str = "",
        context: str = "",
        precision: str = "",
    ) -> dict:
        """Produce a Fermi estimate."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FERMI_PROMPT.format(
                question=question,
                domain=domain or "general",
                context=context or "No additional context",
                precision=precision or "Order of magnitude",
            ),
            system=FERMI_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)

        decomposition = data.get("decomposition", [])
        return {
            "question": question[:200],
            "factors_count": len(decomposition),
            "decomposition": decomposition,
            "calculation": data.get("calculation", ""),
            "point_estimate": data.get("point_estimate", 0),
            "low_bound": data.get("low_bound", 0),
            "high_bound": data.get("high_bound", 0),
            "unit": data.get("unit", ""),
            "order_of_magnitude": data.get("order_of_magnitude", ""),
            "most_uncertain_factor": data.get("most_uncertain_factor", ""),
            "sanity_checks": data.get("sanity_checks", []),
        }
