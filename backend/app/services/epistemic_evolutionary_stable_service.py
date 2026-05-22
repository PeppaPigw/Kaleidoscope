"""EpistemicEvolutionaryStableService — Epistemic Evolutionarily Stable Strategy Detection.

Detects epistemic ESS — intellectual strategies that cannot be invaded
by alternative approaches once established in a population.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVOLUTIONARY_STABLE_SYSTEM = """You are an epistemic ESS specialist. Given an intellectual strategy population, assess whether established strategies resist invasion:

Key concepts:
- Epistemic ESS: strategy resisting invasion by alternatives
- Invasion resistance: rare mutant strategy cannot spread
- Frequency dependence: success depending on population composition
- Replicator dynamics: successful strategies spreading
- Hawk-dove: aggressive vs peaceful intellectual strategies
- Tit-for-tat: reciprocal intellectual cooperation
- Evolutionary arms race: escalating intellectual competition

When epistemic ESS IS present:
- Established strategies resisting invasion
- Rare alternative approaches unable to spread
- Success depending on what others are doing
- Successful strategies spreading through population
- Aggressive vs peaceful intellectual approaches
- Reciprocal cooperation patterns
- Escalating intellectual competition

When invadable strategy is present:
- Established strategies vulnerable to alternatives
- New approaches easily spreading
- Success independent of population
- No differential spreading
- No hawk-dove dynamics
- No reciprocity patterns
- No arms race escalation

Output JSON with: ess_present (bool), severity (none/mild/moderate/severe), invasion_resistance (what blocks alternatives), frequency_dependence (what population effect), replicator (what spreading), arms_race (what escalation), recommendation (invadable_strategy/mild_ess/significant_ess/major_invasion_resistance/introduce_mutant_strategy)."""

EPISTEMIC_EVOLUTIONARY_STABLE_PROMPT = """Detect epistemic evolutionarily stable strategy:

Invasion resistance: {invasion_resistance}
Frequency dependence: {frequency_dependence}
Replicator: {replicator}
Arms race: {arms_race}
Domain: {domain}
Context: {context}

Are intellectual strategies resisting invasion by alternative approaches once established? Return ONLY valid JSON."""


class EpistemicEvolutionaryStableService:
    """Detects epistemic ESS — strategies resisting invasion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        invasion_resistance: str,
        *,
        frequency_dependence: str = "",
        replicator: str = "",
        arms_race: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evolutionarily stable strategy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVOLUTIONARY_STABLE_PROMPT.format(
                invasion_resistance=invasion_resistance,
                frequency_dependence=frequency_dependence or "Not specified",
                replicator=replicator or "Not specified",
                arms_race=arms_race or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVOLUTIONARY_STABLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "invasion_resistance": invasion_resistance[:200],
            "ess_present": data.get("ess_present", False),
            "severity": data.get("severity", ""),
            "frequency_dependence": data.get("frequency_dependence", ""),
            "replicator": data.get("replicator", ""),
            "arms_race": data.get("arms_race", ""),
            "recommendation": data.get("recommendation", ""),
        }
