"""NonlinearityNeglectService — Nonlinearity Neglect Detection.

Detects nonlinearity neglect — assuming linear relationships
when the system exhibits nonlinear behavior such as thresholds,
exponential growth, saturation, or phase transitions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NONLINEARITY_NEGLECT_SYSTEM = """You are a nonlinearity neglect specialist. Given a prediction or model, assess whether nonlinear effects are being ignored:

Key concepts:
- Nonlinearity: output not proportional to input
- Thresholds: nothing happens until a critical point
- Exponential growth: doubling behavior
- Saturation: diminishing returns at high levels
- Phase transitions: qualitative changes at critical values
- Tipping points: small changes causing large effects
- Linear extrapolation error: assuming proportionality

When nonlinearity neglect IS present:
- Linear model applied to nonlinear system
- Proportional thinking where thresholds exist
- Exponential growth treated as linear
- Saturation effects ignored
- Phase transitions not anticipated
- Small changes assumed to have small effects (near tipping points)
- Extrapolation assumes constant rate of change

When nonlinearity is recognized:
- Nonlinear relationships explicitly modeled
- Thresholds and tipping points identified
- Exponential behavior recognized and modeled
- Saturation and diminishing returns accounted for
- Phase transitions anticipated
- Sensitivity to initial conditions acknowledged
- Appropriate nonlinear models used

Output JSON with: neglect_present (bool), severity (none/mild/moderate/severe), relationship (what relationship is being modeled), nonlinearity_type (threshold/exponential/saturation/phase_transition), linear_assumption (what linear model is being used), actual_behavior (what the nonlinear behavior is), recommendation (nonlinearity_recognized/mild_linearization/significant_neglect/major_linear_error/model_nonlinearly)."""

NONLINEARITY_NEGLECT_PROMPT = """Detect nonlinearity neglect:

Model: {model}
Relationship: {relationship}
Assumptions: {assumptions}
Observed behavior: {behavior}
Domain: {domain}
Context: {context}

Are nonlinear effects being ignored in this model? Return ONLY valid JSON."""


class NonlinearityNeglectService:
    """Detects nonlinearity neglect — assuming linear when system is nonlinear."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        model: str,
        *,
        relationship: str = "",
        assumptions: str = "",
        behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect nonlinearity neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NONLINEARITY_NEGLECT_PROMPT.format(
                model=model,
                relationship=relationship or "Not specified",
                assumptions=assumptions or "Not specified",
                behavior=behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NONLINEARITY_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "model": model[:200],
            "neglect_present": data.get("neglect_present", False),
            "severity": data.get("severity", ""),
            "nonlinearity_type": data.get("nonlinearity_type", ""),
            "linear_assumption": data.get("linear_assumption", ""),
            "actual_behavior": data.get("actual_behavior", ""),
            "recommendation": data.get("recommendation", ""),
        }
