"""EpistemicThermalEquilibriumService — Epistemic Thermal Equilibrium Detection.

Detects epistemic thermal equilibrium — all ideas reaching the same
temperature, losing useful gradients that drive intellectual work.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_THERMAL_EQUILIBRIUM_SYSTEM = """You are an epistemic thermal equilibrium specialist. Given an intellectual ecosystem, assess whether useful gradients have been lost:

Key concepts:
- Epistemic thermal equilibrium: all ideas at same temperature, no useful gradients
- Gradient loss: losing the differences that drive intellectual work
- Intellectual heat death: state where no useful work can be done
- Uniform temperature: all ideas treated with same weight/urgency
- No flow: no intellectual energy flowing between ideas
- Stasis: intellectual stasis from lack of gradients
- Differentiation loss: losing ability to distinguish important from trivial

When thermal equilibrium IS present:
- All ideas at same temperature/priority
- Useful gradients between ideas lost
- No intellectual energy flowing productively
- Everything treated with same weight
- Intellectual stasis from lack of differentiation
- No driving force for intellectual work
- Important and trivial ideas indistinguishable

When productive gradients are present:
- Ideas at different temperatures/priorities
- Useful gradients driving intellectual work
- Intellectual energy flowing productively
- Different weights for different ideas
- Active intellectual work driven by gradients
- Clear driving forces for progress
- Important ideas distinguished from trivial

Output JSON with: equilibrium_present (bool), severity (none/mild/moderate/severe), ecosystem (what ecosystem is in equilibrium), gradient_loss (what gradients are lost), stasis (what stasis results), differentiation (what differentiation is lost), recommendation (productive_gradients/mild_equilibrium/significant_gradient_loss/major_heat_death/restore_differentiation)."""

EPISTEMIC_THERMAL_EQUILIBRIUM_PROMPT = """Detect epistemic thermal equilibrium:

Ecosystem: {ecosystem}
Gradient loss: {gradient_loss}
Stasis: {stasis}
Differentiation: {differentiation}
Domain: {domain}
Context: {context}

Have all ideas reached the same temperature, losing useful gradients that drive work? Return ONLY valid JSON."""


class EpistemicThermalEquilibriumService:
    """Detects epistemic thermal equilibrium — loss of useful intellectual gradients."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ecosystem: str,
        *,
        gradient_loss: str = "",
        stasis: str = "",
        differentiation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic thermal equilibrium."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_THERMAL_EQUILIBRIUM_PROMPT.format(
                ecosystem=ecosystem,
                gradient_loss=gradient_loss or "Not specified",
                stasis=stasis or "Not specified",
                differentiation=differentiation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_THERMAL_EQUILIBRIUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ecosystem": ecosystem[:200],
            "equilibrium_present": data.get("equilibrium_present", False),
            "severity": data.get("severity", ""),
            "gradient_loss": data.get("gradient_loss", ""),
            "stasis": data.get("stasis", ""),
            "differentiation": data.get("differentiation", ""),
            "recommendation": data.get("recommendation", ""),
        }
