"""EpistemicNashEquilibriumService — Epistemic Nash Equilibrium Detection.

Detects epistemic Nash equilibrium — intellectual positions where no
participant can improve their position by unilaterally changing strategy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NASH_EQUILIBRIUM_SYSTEM = """You are an epistemic Nash equilibrium specialist. Given an intellectual interaction, assess whether positions are in equilibrium:

Key concepts:
- Epistemic Nash equilibrium: no unilateral improvement possible
- Best response: optimal strategy given others' strategies
- Dominant strategy: best regardless of others' choices
- Mixed strategy: randomizing between options
- Pareto efficiency: no improvement without harming another
- Coordination game: benefit from matching strategies
- Prisoner's dilemma: individual incentive vs collective good

When epistemic Nash equilibrium IS present:
- No participant can improve by changing alone
- Each position is best response to others
- Dominant strategies locking in positions
- Randomization between intellectual options
- No improvement possible without harming someone
- Benefit from matching intellectual strategies
- Individual incentives opposing collective good

When disequilibrium is present:
- Participants can improve by changing strategy
- Positions not best responses to others
- No dominant strategies
- Pure deterministic choices
- Improvements possible for all
- No coordination benefits
- Individual and collective incentives aligned

Output JSON with: nash_equilibrium_present (bool), severity (none/mild/moderate/severe), best_response (what optimal strategy), dominant (what locked strategy), pareto (what efficiency), coordination (what matching benefit), recommendation (disequilibrium/mild_equilibrium/significant_nash_equilibrium/major_strategic_lock/break_equilibrium)."""

EPISTEMIC_NASH_EQUILIBRIUM_PROMPT = """Detect epistemic Nash equilibrium:

Best response: {best_response}
Dominant: {dominant}
Pareto: {pareto}
Coordination: {coordination}
Domain: {domain}
Context: {context}

Are intellectual positions in equilibrium where no participant can improve by unilaterally changing strategy? Return ONLY valid JSON."""


class EpistemicNashEquilibriumService:
    """Detects epistemic Nash equilibrium — no unilateral improvement possible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        best_response: str,
        *,
        dominant: str = "",
        pareto: str = "",
        coordination: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Nash equilibrium."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NASH_EQUILIBRIUM_PROMPT.format(
                best_response=best_response,
                dominant=dominant or "Not specified",
                pareto=pareto or "Not specified",
                coordination=coordination or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NASH_EQUILIBRIUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "best_response": best_response[:200],
            "nash_equilibrium_present": data.get("nash_equilibrium_present", False),
            "severity": data.get("severity", ""),
            "dominant": data.get("dominant", ""),
            "pareto": data.get("pareto", ""),
            "coordination": data.get("coordination", ""),
            "recommendation": data.get("recommendation", ""),
        }
