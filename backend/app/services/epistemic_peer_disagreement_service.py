"""EpistemicPeerDisagreementService — Epistemic Peer Disagreement Detection.

Detects epistemic peer disagreement issues — how to handle disagreement
with equally qualified people. When genuine epistemic peers disagree,
simply maintaining your position without updating may indicate
overconfidence in your own reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PEER_SYSTEM = """You are an epistemic peer disagreement specialist. Given a disagreement, assess whether the parties are genuine epistemic peers and whether the disagreement is being handled appropriately:

Key concepts:
- Epistemic peer: someone with equal evidence, intelligence, and good faith
- Conciliationism: peers should move toward each other's positions
- Steadfastness: sometimes maintaining your position is justified
- Peer identification: are they really your epistemic peer on this topic?
- Asymmetric confidence: one party may have private reasons for confidence
- Higher-order evidence: disagreement itself is evidence about your reliability
- Rational disagreement: can peers rationally disagree after full disclosure?

When peer disagreement is handled poorly:
- Dismissing a genuine peer's view without updating at all
- Assuming you must be right because you're you
- Failing to consider that disagreement is evidence of your own error
- "They're smart but wrong" without explaining why you're more likely right
- Ignoring the base rate of being wrong when peers disagree
- Treating all disagreement as if the other person is less informed
- Not distinguishing between peers and non-peers

When maintaining position IS appropriate:
- You have private evidence the peer lacks (and can articulate it)
- The peer has a known bias on this specific topic
- You've genuinely considered their view and can explain why it fails
- The disagreement is about values, not facts
- You've identified a specific error in their reasoning
- Track record on this type of question favors your approach
- The "peer" is actually not a peer on this specific topic

Output JSON with: peer_disagreement_issue (bool), severity (none/mild/moderate/severe), disagreement (what is being disagreed about), peer_status (are they genuine epistemic peers), handling (how is the disagreement being handled), updating (is either party updating based on the disagreement), asymmetry (what asymmetry justifies different positions), recommendation (handling_appropriate/mild_overconfidence/significant_peer_dismissal/major_epistemic_arrogance/update_toward_peer_or_explain_asymmetry)."""

EPISTEMIC_PEER_PROMPT = """Detect epistemic peer disagreement issues:

Disagreement: {disagreement}
Peer status: {peer_status}
Handling: {handling}
Updating: {updating}
Domain: {domain}
Context: {context}

Is disagreement with an epistemic peer being handled appropriately? Return ONLY valid JSON."""


class EpistemicPeerDisagreementService:
    """Detects epistemic peer disagreement handling issues."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        disagreement: str,
        *,
        peer_status: str = "",
        handling: str = "",
        updating: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic peer disagreement issues."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PEER_PROMPT.format(
                disagreement=disagreement,
                peer_status=peer_status or "Not specified",
                handling=handling or "Not specified",
                updating=updating or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PEER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "disagreement": disagreement[:200],
            "peer_disagreement_issue": data.get("peer_disagreement_issue", False),
            "severity": data.get("severity", ""),
            "peer_status": data.get("peer_status", ""),
            "handling": data.get("handling", ""),
            "updating": data.get("updating", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
