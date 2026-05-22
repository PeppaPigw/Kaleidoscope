"""DoorInFaceService — Door-in-the-Face Technique Detection.

Detects door-in-the-face technique — making an extreme initial
request that will be refused, followed by a smaller request
that seems reasonable by comparison. Cialdini et al. (1975).
The contrast makes the second request feel like a concession,
triggering reciprocity. "Can you donate $500? No? How about $20?"
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DOOR_IN_FACE_SYSTEM = """You are a door-in-the-face technique specialist. Given a sequence of requests or negotiations, assess whether an extreme initial request is being used to make a subsequent request seem more reasonable:

Key concepts (Cialdini et al., 1975):
- Door-in-the-face: extreme request → refusal → moderate request → compliance
- Reciprocal concession: feeling obligated to reciprocate the "concession"
- Perceptual contrast: second request seems small compared to first
- Guilt reduction: refusing first request creates guilt
- Anchoring interaction: extreme first request anchors expectations
- Negotiation tactic: starting high to settle in the middle
- Sequential request strategy: planned sequence of asks

When door-in-the-face IS present:
- An extreme initial request followed by a "reasonable" one
- "Since you can't do X, could you at least do Y?"
- Negotiations starting with extreme positions to anchor
- Feeling obligated after refusing the first request
- The moderate request was the actual goal all along
- Contrast making a significant request feel small
- "I've already come down from my original ask"

When the sequence IS legitimate:
- The initial request was genuine, not strategic
- The person genuinely adjusted expectations based on feedback
- The second request is independently reasonable
- There's no manipulation intent in the sequence
- The negotiation reflects genuine preference discovery

Output JSON with: door_in_face_present (bool), severity (none/mild/moderate/severe), situation (what request sequence is occurring), initial_request (what was the extreme first request), actual_request (what is the real request), contrast_effect (how much does contrast influence perception), reciprocity_pressure (is reciprocal concession being triggered), strategic_intent (was the sequence planned), recommendation (sequence_legitimate/mild_contrast/significant_manipulation/major_door_in_face/evaluate_request_independently)."""

DOOR_IN_FACE_PROMPT = """Detect door-in-the-face technique:

Situation: {situation}
Initial request: {initial}
Follow-up request: {followup}
Response pattern: {response}
Domain: {domain}
Context: {context}

Is an extreme initial request being used to make a subsequent request seem reasonable? Return ONLY valid JSON."""


class DoorInFaceService:
    """Detects door-in-the-face technique — extreme request making moderate one seem reasonable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        initial: str = "",
        followup: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect door-in-the-face technique."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DOOR_IN_FACE_PROMPT.format(
                situation=situation,
                initial=initial or "Not specified",
                followup=followup or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DOOR_IN_FACE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "door_in_face_present": data.get("door_in_face_present", False),
            "severity": data.get("severity", ""),
            "initial_request": data.get("initial_request", ""),
            "actual_request": data.get("actual_request", ""),
            "contrast_effect": data.get("contrast_effect", ""),
            "reciprocity_pressure": data.get("reciprocity_pressure", ""),
            "strategic_intent": data.get("strategic_intent", ""),
            "recommendation": data.get("recommendation", ""),
        }
