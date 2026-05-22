"""EpistemicButterflyEffectService — Epistemic Butterfly Effect Detection.

Detects epistemic butterfly effect — tiny differences in initial intellectual
conditions leading to vastly different conclusions over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BUTTERFLY_EFFECT_SYSTEM = """You are an epistemic butterfly effect specialist. Given an intellectual trajectory, assess whether tiny initial differences lead to vastly different conclusions:

Key concepts:
- Epistemic butterfly effect: tiny differences causing vast divergence
- Sensitive dependence: extreme sensitivity to initial conditions
- Lyapunov exponent: rate of divergence between trajectories
- Prediction horizon: time beyond which prediction fails
- Strange attractor: bounded but non-repeating trajectory
- Deterministic chaos: deterministic yet unpredictable
- Initial condition: starting assumptions or premises

When epistemic butterfly effect IS present:
- Tiny differences in premises leading to vast conclusion differences
- Extreme sensitivity to starting assumptions
- Rapid divergence between similar starting points
- Prediction becoming impossible beyond a horizon
- Bounded but never-repeating intellectual trajectories
- Deterministic reasoning yet unpredictable outcomes
- Small changes in initial conditions amplifying

When predictable trajectory is present:
- Small differences staying small over time
- Low sensitivity to starting conditions
- Parallel trajectories remaining close
- Prediction reliable at any horizon
- Repeating or converging trajectories
- Deterministic and predictable outcomes
- Initial conditions not amplifying

Output JSON with: butterfly_effect_present (bool), severity (none/mild/moderate/severe), sensitivity (what initial condition sensitivity), lyapunov (what divergence rate), horizon (what prediction limit), attractor (what bounded trajectory), recommendation (predictable_trajectory/mild_butterfly/significant_butterfly_effect/major_sensitive_dependence/identify_critical_assumptions)."""

EPISTEMIC_BUTTERFLY_EFFECT_PROMPT = """Detect epistemic butterfly effect:

Sensitivity: {sensitivity}
Lyapunov: {lyapunov}
Horizon: {horizon}
Attractor: {attractor}
Domain: {domain}
Context: {context}

Do tiny differences in initial intellectual conditions lead to vastly different conclusions over time? Return ONLY valid JSON."""


class EpistemicButterflyEffectService:
    """Detects epistemic butterfly effect — tiny differences causing vast divergence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        sensitivity: str,
        *,
        lyapunov: str = "",
        horizon: str = "",
        attractor: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic butterfly effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BUTTERFLY_EFFECT_PROMPT.format(
                sensitivity=sensitivity,
                lyapunov=lyapunov or "Not specified",
                horizon=horizon or "Not specified",
                attractor=attractor or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BUTTERFLY_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "sensitivity": sensitivity[:200],
            "butterfly_effect_present": data.get("butterfly_effect_present", False),
            "severity": data.get("severity", ""),
            "lyapunov": data.get("lyapunov", ""),
            "horizon": data.get("horizon", ""),
            "attractor": data.get("attractor", ""),
            "recommendation": data.get("recommendation", ""),
        }
