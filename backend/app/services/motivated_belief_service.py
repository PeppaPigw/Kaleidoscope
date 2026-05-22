"""MotivatedBeliefService — Motivated Belief Detection.

Detects motivated belief — believing something because it is desired
rather than because evidence supports it, where the wish is father
to the thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_BELIEF_SYSTEM = """You are a motivated belief specialist. Given a belief, assess whether it is held because desired rather than evidenced:

Key concepts:
- Motivated belief: believing because wanting to believe
- Wishful thinking: desire driving belief
- Desire-evidence confusion: wanting confused with knowing
- Comfort-driven belief: believing for emotional comfort
- Interest-driven belief: believing what serves interests
- Hope as evidence: treating hope as reason to believe
- Outcome-dependent belief: belief tracking desired outcomes

When motivated belief IS present:
- Belief held primarily because desired
- Evidence insufficient but desire fills the gap
- Wanting confused with having reason to believe
- Emotional comfort driving belief formation
- Self-interest shaping what is believed
- Hope treated as evidence
- Belief tracks what's desired not what's supported

When belief happens to align with desire:
- Evidence independently supports the belief
- Desire acknowledged but not driving belief
- Belief would survive if desire changed
- Evidence evaluated regardless of preference
- Uncomfortable implications accepted
- Belief formation independent of outcome preference
- Counter-evidence genuinely considered

Output JSON with: motivated_present (bool), severity (none/mild/moderate/severe), belief (what is believed), desire (what is desired), evidence (what evidence exists), gap (what gap desire fills), recommendation (evidence_based_belief/mild_wishful_thinking/significant_motivated_belief/major_desire_driven_belief/separate_desire_from_evidence)."""

MOTIVATED_BELIEF_PROMPT = """Detect motivated belief:

Belief: {belief}
Desire: {desire}
Evidence available: {evidence}
Counter-evidence: {counter}
Domain: {domain}
Context: {context}

Is this belief held because desired rather than evidenced? Return ONLY valid JSON."""


class MotivatedBeliefService:
    """Detects motivated belief — believing because desired not evidenced."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        desire: str = "",
        evidence: str = "",
        counter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated belief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_BELIEF_PROMPT.format(
                belief=belief,
                desire=desire or "Not specified",
                evidence=evidence or "Not specified",
                counter=counter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_BELIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "motivated_present": data.get("motivated_present", False),
            "severity": data.get("severity", ""),
            "desire": data.get("desire", ""),
            "evidence": data.get("evidence", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
