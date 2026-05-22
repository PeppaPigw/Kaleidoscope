"""EpistemicPerformativeBeliefService — Epistemic Performative Belief Detection.

Detects epistemic performative belief — performing beliefs for social
approval rather than genuinely holding them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PERFORMATIVE_BELIEF_SYSTEM = """You are an epistemic performative belief specialist. Given performing beliefs for approval, assess performative belief:

Key concepts:
- Epistemic performative belief: performing beliefs for social approval
- Virtue signaling: displaying beliefs to signal group membership
- Belief theater: acting out convictions not genuinely held
- Social conformity: adopting beliefs to fit in
- Audience-dependent belief: changing stated beliefs by audience
- Performative certainty: displaying confidence not genuinely felt
- Identity performance: beliefs as identity costume not genuine conviction

When epistemic performative belief IS present:
- Performing beliefs for approval
- Displaying beliefs for group membership
- Acting out convictions not held
- Adopting beliefs to fit in
- Changing beliefs by audience
- Displaying false confidence
- Beliefs as costume not conviction

When no performative belief:
- Genuine belief expression
- Authentic group participation
- Sincere convictions
- Independent belief formation
- Consistent across audiences
- Honest confidence levels
- Beliefs as genuine identity

Output JSON with: performative_belief_detected (bool), severity (none/mild/moderate/severe), virtue_signaling (what displaying for membership), belief_theater (what acting out), audience_dependent (what changing by audience), performative_certainty (what false confidence about), recommendation (no_performative_belief/mild_authenticity_check/significant_sincerity_building/major_intensive_authenticity_work/emergency_complete_belief_performance)."""

EPISTEMIC_PERFORMATIVE_BELIEF_PROMPT = """Detect epistemic performative belief:

Virtue signaling: {virtue_signaling}
Belief theater: {belief_theater}
Audience dependent: {audience_dependent}
Performative certainty: {performative_certainty}
Domain: {domain}
Context: {context}

Is there performing beliefs for social approval rather than genuine conviction? Return ONLY valid JSON."""


class EpistemicPerformativeBeliefService:
    """Detects epistemic performative belief — performing beliefs for approval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        virtue_signaling: str,
        *,
        belief_theater: str = "",
        audience_dependent: str = "",
        performative_certainty: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic performative belief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PERFORMATIVE_BELIEF_PROMPT.format(
                virtue_signaling=virtue_signaling,
                belief_theater=belief_theater or "Not specified",
                audience_dependent=audience_dependent or "Not specified",
                performative_certainty=performative_certainty or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PERFORMATIVE_BELIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "virtue_signaling": virtue_signaling[:200],
            "performative_belief_detected": data.get("performative_belief_detected", False),
            "severity": data.get("severity", ""),
            "belief_theater": data.get("belief_theater", ""),
            "audience_dependent": data.get("audience_dependent", ""),
            "performative_certainty": data.get("performative_certainty", ""),
            "recommendation": data.get("recommendation", ""),
        }
