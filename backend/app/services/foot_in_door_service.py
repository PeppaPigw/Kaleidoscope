"""FootInDoorService — Foot-in-the-Door Technique Detection.

Detects foot-in-the-door technique — getting compliance with
a small initial request to increase likelihood of compliance
with a larger subsequent request. Freedman & Fraser (1966).
Once someone says yes to something small, they're more likely
to say yes to something big to remain consistent with their
self-image as helpful/agreeable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FOOT_IN_DOOR_SYSTEM = """You are a foot-in-the-door technique specialist. Given a sequence of escalating requests, assess whether small initial compliance is being used to secure larger commitments:

Key concepts (Freedman & Fraser, 1966):
- Foot-in-the-door: small request → compliance → larger request → compliance
- Self-perception: "I'm the kind of person who helps/agrees"
- Commitment escalation: each yes makes the next yes easier
- Consistency pressure: desire to be consistent with past behavior
- Incremental commitment: gradually increasing asks
- Behavioral momentum: pattern of compliance continues
- Identity shift: small actions change self-concept

When foot-in-the-door IS present:
- Small initial requests followed by escalating demands
- "Since you already agreed to X, would you also do Y?"
- Gradual escalation of commitment over time
- Using past compliance as leverage for new requests
- "You've already invested so much, why stop now?"
- Small favors building toward large obligations
- Identity being shaped by initial small commitments

When the escalation IS natural:
- Requests grow naturally with the relationship
- Each request is independently justified
- The person freely chooses at each step without pressure
- There's no strategic intent in the sequence
- The escalation reflects genuine growing needs

Output JSON with: foot_in_door_present (bool), severity (none/mild/moderate/severe), situation (what request sequence is occurring), initial_request (what was the small first request), escalated_request (what is the larger request), consistency_pressure (is consistency being leveraged), identity_shift (has self-perception changed), escalation_rate (how quickly are requests growing), recommendation (escalation_natural/mild_technique/significant_manipulation/major_foot_in_door/evaluate_each_request_independently)."""

FOOT_IN_DOOR_PROMPT = """Detect foot-in-the-door technique:

Situation: {situation}
Initial request: {initial}
Current request: {current}
History: {history}
Domain: {domain}
Context: {context}

Is small initial compliance being used to secure larger commitments? Return ONLY valid JSON."""


class FootInDoorService:
    """Detects foot-in-the-door technique — small compliance escalating to large."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        initial: str = "",
        current: str = "",
        history: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect foot-in-the-door technique."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FOOT_IN_DOOR_PROMPT.format(
                situation=situation,
                initial=initial or "Not specified",
                current=current or "Not specified",
                history=history or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FOOT_IN_DOOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "foot_in_door_present": data.get("foot_in_door_present", False),
            "severity": data.get("severity", ""),
            "initial_request": data.get("initial_request", ""),
            "escalated_request": data.get("escalated_request", ""),
            "consistency_pressure": data.get("consistency_pressure", ""),
            "identity_shift": data.get("identity_shift", ""),
            "escalation_rate": data.get("escalation_rate", ""),
            "recommendation": data.get("recommendation", ""),
        }
