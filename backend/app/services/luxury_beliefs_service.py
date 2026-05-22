"""LuxuryBeliefsService — Luxury Beliefs Detection.

Detects luxury beliefs — ideas and opinions that confer status on the
holder while imposing costs on others who lack the resources to insulate
themselves from the consequences. Henderson (2019).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LUXURY_BELIEFS_SYSTEM = """You are a luxury beliefs specialist. Given a belief or position, assess whether it functions as a luxury belief — conferring status on the holder while imposing costs on others:

Key concepts (Henderson, 2019):
- Luxury belief: idea that confers status on the affluent while harming the less privileged
- Status signaling: beliefs held primarily for social positioning
- Insulation: the holder is protected from the consequences of the belief
- Cost externalization: negative effects fall on those who can't afford them
- Virtue signaling vs. virtue: expressing values without bearing costs
- Class markers: beliefs that function as indicators of social class
- Skin in the game: whether the believer bears consequences of the belief

When luxury belief IS present:
- The holder is insulated from the consequences of the belief
- Costs of the belief fall disproportionately on the less privileged
- The belief functions primarily as a status marker
- The holder would likely change their view if they bore the costs
- There's a gap between the stated belief and the holder's actual behavior
- The belief is popular among those who won't experience its effects
- Advocacy without personal sacrifice or exposure to consequences

When the belief IS genuinely held:
- The holder bears real costs for holding the belief
- The belief is consistent with the holder's behavior
- The holder has skin in the game regarding consequences
- The belief is held across socioeconomic strata
- Evidence supports the belief independent of status signaling
- The holder acknowledges and addresses distributional effects
- Personal sacrifice accompanies the advocacy

Output JSON with: luxury_belief_present (bool), severity (none/mild/moderate/severe), belief (what belief is held), status_function (how it confers status), cost_distribution (who bears the costs), insulation (how holder is protected), behavior_consistency (does behavior match belief), recommendation (belief_genuine/mild_status_signaling/significant_luxury_belief/major_cost_externalization/examine_who_bears_costs)."""

LUXURY_BELIEFS_PROMPT = """Detect luxury beliefs:

Belief: {belief}
Holder context: {holder}
Costs: {costs}
Insulation: {insulation}
Domain: {domain}
Context: {context}

Does this belief function as a luxury belief — conferring status while externalizing costs? Return ONLY valid JSON."""


class LuxuryBeliefsService:
    """Detects luxury beliefs — status-conferring ideas that impose costs on others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        holder: str = "",
        costs: str = "",
        insulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect luxury beliefs."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LUXURY_BELIEFS_PROMPT.format(
                belief=belief,
                holder=holder or "Not specified",
                costs=costs or "Not specified",
                insulation=insulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LUXURY_BELIEFS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "luxury_belief_present": data.get("luxury_belief_present", False),
            "severity": data.get("severity", ""),
            "status_function": data.get("status_function", ""),
            "cost_distribution": data.get("cost_distribution", ""),
            "insulation": data.get("insulation", ""),
            "behavior_consistency": data.get("behavior_consistency", ""),
            "recommendation": data.get("recommendation", ""),
        }
