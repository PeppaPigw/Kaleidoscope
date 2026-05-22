"""LuxuryBeliefService — Luxury Belief Detection.

Detects luxury beliefs — ideas and opinions that confer status
on the holder while imposing costs on lower classes. Henderson
(2019). Upper-class people can afford the consequences of certain
beliefs; lower-class people cannot. The belief signals virtue
while its real-world effects fall on others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LUXURY_BELIEF_SYSTEM = """You are a luxury belief specialist. Given a belief or position, assess whether it confers status on the holder while imposing costs on others:

Key concepts (Henderson, 2019):
- Luxury belief: confers status on holder, costs fall on others
- Status signaling: beliefs as markers of class/education
- Insulation from consequences: holder doesn't bear the costs
- Virtue signaling: displaying moral superiority without cost
- Class asymmetry: different classes bear different consequences
- Skin in the game: whether the believer faces consequences
- Performative belief: held for social benefit, not truth value

When luxury belief IS present:
- The holder is insulated from the consequences of the belief
- The belief signals education/class/sophistication
- Real-world costs fall disproportionately on others
- The holder would change the belief if they bore the costs
- The belief is more common among those insulated from its effects
- Advocating policies whose costs one won't personally bear
- The belief functions as a status marker in social circles

When the belief IS genuinely held:
- The holder bears proportional consequences
- The belief is held consistently regardless of personal cost
- The holder has skin in the game
- The belief is based on evidence, not social signaling
- Costs and benefits are distributed fairly
- The holder acknowledges and accepts personal costs

Output JSON with: luxury_belief_present (bool), severity (none/mild/moderate/severe), belief (what belief is being held), status_signal (what status does it confer), cost_bearer (who bears the costs), holder_insulation (how is the holder insulated), class_asymmetry (how do consequences differ by class), skin_in_game (does the holder face consequences), recommendation (belief_genuine/mild_status_signaling/significant_luxury_belief/major_cost_externalization/acknowledge_asymmetric_consequences)."""

LUXURY_BELIEF_PROMPT = """Detect luxury belief:

Belief: {belief}
Holder: {holder}
Consequences: {consequences}
Cost distribution: {cost_distribution}
Domain: {domain}
Context: {context}

Does this belief confer status on the holder while imposing costs on others? Return ONLY valid JSON."""


class LuxuryBeliefService:
    """Detects luxury beliefs — status-conferring beliefs with externalized costs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        holder: str = "",
        consequences: str = "",
        cost_distribution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect luxury belief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LUXURY_BELIEF_PROMPT.format(
                belief=belief,
                holder=holder or "Not specified",
                consequences=consequences or "Not specified",
                cost_distribution=cost_distribution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LUXURY_BELIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "luxury_belief_present": data.get("luxury_belief_present", False),
            "severity": data.get("severity", ""),
            "status_signal": data.get("status_signal", ""),
            "cost_bearer": data.get("cost_bearer", ""),
            "holder_insulation": data.get("holder_insulation", ""),
            "class_asymmetry": data.get("class_asymmetry", ""),
            "skin_in_game": data.get("skin_in_game", ""),
            "recommendation": data.get("recommendation", ""),
        }
