"""IllusionOfTransparencyService — Illusion of Transparency Detection.

Detects the illusion of transparency — overestimating how well
others can read your internal states (emotions, intentions,
knowledge). Gilovich, Savitsky & Medvec (1998). You think your
nervousness is obvious, your sarcasm is clear, your hints are
understood. Related to curse of knowledge but specifically about
emotional/intentional states rather than factual knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRANSPARENCY_SYSTEM = """You are an illusion of transparency specialist. Given a communication or social situation, assess whether the illusion of transparency is creating misunderstanding:

Key concepts (Gilovich, Savitsky & Medvec, 1998):
- Illusion of transparency: overestimating how visible your internal states are to others
- Spotlight effect overlap: believing others notice you more than they do
- Signal clarity overestimation: thinking your hints, tone, and intentions are obvious
- Anchoring on own experience: your feelings are vivid to you, so they must be visible
- Curse of knowledge overlap: but specifically about emotional/intentional states
- Communication failure: "I made it clear" when you didn't

When the illusion IS present:
- Assuming others can tell how you feel without explicit communication
- Believing hints or indirect communication was understood
- Thinking intentions are obvious from behavior
- Expecting others to "just know" without being told
- Surprise that others misread your emotional state
- "I thought it was obvious that I was being sarcastic/serious/joking"

When transparency IS real:
- Explicit verbal communication of internal states
- Long-established relationships with proven mutual understanding
- Very strong emotional displays that are genuinely hard to miss
- Cultural contexts where certain signals are universally understood
- Feedback confirms the message was received as intended

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), internal_state (what the person thinks is visible), actual_visibility (how visible it actually is to others), communication_gap (what's being assumed vs what's actually communicated), signal_type (verbal/nonverbal/contextual/implicit), signal_clarity (how clear the signal actually is), receiver_perspective (what the other person likely perceives), anchoring_on_self (bool — projecting own vivid experience onto others?), explicit_communication (bool — was the state explicitly stated?), feedback_received (bool — has understanding been confirmed?), relationship_context (how well do the parties know each other?), consequences (what happens because of the miscommunication), recommendation (communication_clear/mild_overestimation/significant_illusion/major_communication_gap/communicate_explicitly)."""

TRANSPARENCY_PROMPT = """Detect illusion of transparency:

Situation: {situation}
What's assumed visible: {assumed_visible}
Communication method: {communication}
Receiver's perspective: {receiver}
Domain: {domain}
Context: {context}

Is the illusion of transparency creating miscommunication? Return ONLY valid JSON."""


class IllusionOfTransparencyService:
    """Detects illusion of transparency — overestimating visibility of internal states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        assumed_visible: str = "",
        communication: str = "",
        receiver: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusion of transparency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRANSPARENCY_PROMPT.format(
                situation=situation,
                assumed_visible=assumed_visible or "Not specified",
                communication=communication or "Not specified",
                receiver=receiver or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TRANSPARENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "illusion_present": data.get("illusion_present", False),
            "severity": data.get("severity", ""),
            "internal_state": data.get("internal_state", ""),
            "actual_visibility": data.get("actual_visibility", ""),
            "communication_gap": data.get("communication_gap", ""),
            "signal_type": data.get("signal_type", ""),
            "signal_clarity": data.get("signal_clarity", ""),
            "receiver_perspective": data.get("receiver_perspective", ""),
            "anchoring_on_self": data.get("anchoring_on_self", False),
            "explicit_communication": data.get("explicit_communication", False),
            "feedback_received": data.get("feedback_received", False),
            "relationship_context": data.get("relationship_context", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
