"""EpistemicComplexityEquilibriumAssumptionService — Epistemic Complexity Equilibrium Assumption Detection.

Detects epistemic complexity equilibrium assumption — assuming systems are in or
tend toward equilibrium when they may be far-from-equilibrium or path-dependent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_EQUILIBRIUM_ASSUMPTION_SYSTEM = """You are an epistemic complexity equilibrium assumption specialist. Given equilibrium assumptions, assess dynamic state distortion:

Key concepts:
- Epistemic equilibrium assumption: assuming systems tend toward stable states
- Stability assumption: assuming current state is stable equilibrium
- Mean reversion: assuming deviations will revert to historical average
- Self-correction: assuming systems self-correct without intervention
- Path independence: ignoring that history determines current state
- Multiple equilibria blindness: missing that multiple stable states exist
- Far-from-equilibrium blindness: missing that system is in unstable state

When epistemic equilibrium assumption IS present:
- Equilibrium assumed
- Current state assumed stable
- Mean reversion expected
- Self-correction assumed
- Path dependence ignored
- Multiple equilibria missed
- Far-from-equilibrium state missed

When no equilibrium assumption:
- Dynamic state assessed
- Stability tested not assumed
- Mean reversion not assumed
- Self-correction not guaranteed
- Path dependence recognized
- Multiple equilibria considered
- Far-from-equilibrium possible

Output JSON with: equilibrium_assumption_detected (bool), severity (none/mild/moderate/severe), stability_assumption (what stability assumed), mean_reversion (what mean reversion expected), path_independence (what path dependence ignored), multiple_equilibria_blindness (what multiple states missed), recommendation (no_equilibrium_assumption/mild_stability_testing/significant_dynamic_analysis/major_intensive_state_space_mapping/emergency_complete_equilibrium_assumption)."""

EPISTEMIC_COMPLEXITY_EQUILIBRIUM_ASSUMPTION_PROMPT = """Detect epistemic complexity equilibrium assumption:

Stability assumption: {stability_assumption}
Mean reversion: {mean_reversion}
Path independence: {path_independence}
Multiple equilibria blindness: {multiple_equilibria_blindness}
Domain: {domain}
Context: {context}

Are systems being assumed to be in or tend toward equilibrium? Return ONLY valid JSON."""


class EpistemicComplexityEquilibriumAssumptionService:
    """Detects epistemic complexity equilibrium assumption — stability bias."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stability_assumption: str,
        *,
        mean_reversion: str = "",
        path_independence: str = "",
        multiple_equilibria_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity equilibrium assumption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_EQUILIBRIUM_ASSUMPTION_PROMPT.format(
                stability_assumption=stability_assumption,
                mean_reversion=mean_reversion or "Not specified",
                path_independence=path_independence or "Not specified",
                multiple_equilibria_blindness=multiple_equilibria_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_EQUILIBRIUM_ASSUMPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stability_assumption": stability_assumption[:200],
            "equilibrium_assumption_detected": data.get("equilibrium_assumption_detected", False),
            "severity": data.get("severity", ""),
            "mean_reversion": data.get("mean_reversion", ""),
            "path_independence": data.get("path_independence", ""),
            "multiple_equilibria_blindness": data.get("multiple_equilibria_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
