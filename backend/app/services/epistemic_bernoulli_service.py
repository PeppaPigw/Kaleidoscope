"""EpistemicBernoulliService — Epistemic Bernoulli Effect Detection.

Detects epistemic Bernoulli effect — fast-moving ideas creating low
pressure zones that pull surrounding ideas toward them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BERNOULLI_SYSTEM = """You are an epistemic Bernoulli effect specialist. Given an idea flow pattern, assess whether fast-moving ideas create low pressure zones:

Key concepts:
- Epistemic Bernoulli effect: fast ideas creating low pressure
- Velocity: speed of idea movement
- Pressure drop: reduced pressure from fast movement
- Entrainment: surrounding ideas pulled into the flow
- Venturi: narrowing that accelerates ideas
- Lift: upward force from pressure differential
- Stall: loss of lift when flow separates

When epistemic Bernoulli effect IS present:
- Fast-moving ideas creating low pressure zones
- Speed of idea movement affecting surrounding pressure
- Reduced pressure pulling nearby ideas in
- Surrounding ideas entrained by fast-moving ones
- Narrowing channels accelerating idea flow
- Upward force from pressure differences
- Loss of effect when flow separates from surface

When static pressure is present:
- Ideas at rest with uniform pressure
- No speed-related pressure effects
- Uniform pressure throughout
- No entrainment of surrounding ideas
- No acceleration from narrowing
- No lift from pressure differential
- No flow separation possible

Output JSON with: bernoulli_present (bool), severity (none/mild/moderate/severe), velocity (what moves fast), pressure_drop (what low pressure results), entrainment (what gets pulled in), venturi (what narrowing accelerates), recommendation (static_equilibrium/mild_flow_effect/significant_bernoulli/major_pressure_differential/slow_dominant_flow)."""

EPISTEMIC_BERNOULLI_PROMPT = """Detect epistemic Bernoulli effect:

Velocity: {velocity}
Pressure drop: {pressure_drop}
Entrainment: {entrainment}
Venturi: {venturi}
Domain: {domain}
Context: {context}

Are fast-moving ideas creating low pressure zones that pull surrounding ideas toward them? Return ONLY valid JSON."""


class EpistemicBernoulliService:
    """Detects epistemic Bernoulli effect — fast ideas creating low pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        velocity: str,
        *,
        pressure_drop: str = "",
        entrainment: str = "",
        venturi: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Bernoulli effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BERNOULLI_PROMPT.format(
                velocity=velocity,
                pressure_drop=pressure_drop or "Not specified",
                entrainment=entrainment or "Not specified",
                venturi=venturi or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BERNOULLI_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "velocity": velocity[:200],
            "bernoulli_present": data.get("bernoulli_present", False),
            "severity": data.get("severity", ""),
            "pressure_drop": data.get("pressure_drop", ""),
            "entrainment": data.get("entrainment", ""),
            "venturi": data.get("venturi", ""),
            "recommendation": data.get("recommendation", ""),
        }
