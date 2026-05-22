"""EpistemicGriefService — Epistemic Grief Denial Detection.

Detects epistemic grief denial — inability to accept the loss of
cherished beliefs, leading to denial, bargaining, and anger rather
than updating one's worldview in response to disconfirming evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GRIEF_SYSTEM = """You are an epistemic grief denial specialist. Given a belief challenge situation, assess whether grief over lost beliefs is preventing rational update:

Key concepts:
- Epistemic grief denial: refusing to accept belief loss
- Belief bereavement: mourning cherished beliefs
- Worldview threat response: defensive reaction to disconfirmation
- Identity-belief fusion: beliefs so central that loss feels like death
- Bargaining with evidence: trying to save beliefs despite evidence
- Epistemic anger: rage at those who challenge beliefs
- Belief nostalgia: longing for simpler prior worldview

When epistemic grief denial IS present:
- Disconfirming evidence triggers grief response
- Belief loss treated as personal attack
- Bargaining with evidence to save beliefs
- Anger directed at evidence-bearers
- Denial of clear disconfirmation
- Identity threatened by belief update
- Worldview change resisted despite evidence

When belief commitment is appropriate:
- Beliefs held proportionally to evidence
- Disconfirmation processed rationally
- Identity not fused with specific beliefs
- Belief update seen as growth
- Evidence-bearers not attacked
- Worldview flexible and updateable
- Commitment based on evidence not comfort

Output JSON with: grief_present (bool), severity (none/mild/moderate/severe), belief (what belief is challenged), evidence (what disconfirms it), response (what grief response occurs), stage (denial/anger/bargaining/depression/acceptance), recommendation (appropriate_belief_commitment/mild_update_resistance/significant_epistemic_grief/major_belief_denial/process_belief_loss)."""

EPISTEMIC_GRIEF_PROMPT = """Detect epistemic grief denial:

Belief challenged: {belief}
Disconfirming evidence: {evidence}
Response to challenge: {response}
Identity connection: {identity}
Domain: {domain}
Context: {context}

Is grief over lost beliefs preventing rational worldview update? Return ONLY valid JSON."""


class EpistemicGriefService:
    """Detects epistemic grief denial — inability to accept belief loss."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        evidence: str = "",
        response: str = "",
        identity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic grief denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GRIEF_PROMPT.format(
                belief=belief,
                evidence=evidence or "Not specified",
                response=response or "Not specified",
                identity=identity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "grief_present": data.get("grief_present", False),
            "severity": data.get("severity", ""),
            "response": data.get("response", ""),
            "stage": data.get("stage", ""),
            "evidence": data.get("evidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
