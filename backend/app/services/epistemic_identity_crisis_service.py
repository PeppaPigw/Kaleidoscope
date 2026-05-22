"""EpistemicIdentityCrisisService — Epistemic Identity Crisis Detection.

Detects epistemic identity crisis — crisis when core intellectual
beliefs are challenged.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_CRISIS_SYSTEM = """You are an epistemic identity crisis specialist. Given crisis from challenged beliefs, assess identity crisis:

Key concepts:
- Epistemic identity crisis: crisis when core beliefs challenged
- Worldview collapse: entire worldview crumbling from one challenge
- Existential disorientation: losing sense of who one is intellectually
- Belief system failure: core belief system failing under pressure
- Meaning collapse: loss of meaning when beliefs challenged
- Intellectual vertigo: dizzying loss of intellectual ground
- Foundation cracking: foundational beliefs cracking

When epistemic identity crisis IS present:
- Crisis from challenged beliefs
- Worldview crumbling
- Losing sense of intellectual self
- Belief system failing
- Loss of meaning
- Loss of intellectual ground
- Foundations cracking

When no identity crisis:
- Challenges manageable
- Worldview resilient
- Secure intellectual self
- Belief system flexible
- Meaning maintained
- Intellectual ground stable
- Foundations solid

Output JSON with: identity_crisis_detected (bool), severity (none/mild/moderate/severe), worldview_collapse (what worldview crumbling from), existential_disorientation (what losing sense of self about), belief_system_failure (what system failing under), meaning_collapse (what losing meaning from), recommendation (no_identity_crisis/mild_stabilization/significant_reconstruction_support/major_intensive_identity_rebuilding/emergency_complete_identity_crisis)."""

EPISTEMIC_IDENTITY_CRISIS_PROMPT = """Detect epistemic identity crisis:

Worldview collapse: {worldview_collapse}
Existential disorientation: {existential_disorientation}
Belief system failure: {belief_system_failure}
Meaning collapse: {meaning_collapse}
Domain: {domain}
Context: {context}

Is there crisis when core intellectual beliefs are challenged? Return ONLY valid JSON."""


class EpistemicIdentityCrisisService:
    """Detects epistemic identity crisis — crisis when core beliefs challenged."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        worldview_collapse: str,
        *,
        existential_disorientation: str = "",
        belief_system_failure: str = "",
        meaning_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identity crisis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_CRISIS_PROMPT.format(
                worldview_collapse=worldview_collapse,
                existential_disorientation=existential_disorientation or "Not specified",
                belief_system_failure=belief_system_failure or "Not specified",
                meaning_collapse=meaning_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_CRISIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "worldview_collapse": worldview_collapse[:200],
            "identity_crisis_detected": data.get("identity_crisis_detected", False),
            "severity": data.get("severity", ""),
            "existential_disorientation": data.get("existential_disorientation", ""),
            "belief_system_failure": data.get("belief_system_failure", ""),
            "meaning_collapse": data.get("meaning_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }
