"""EpistemicIntrusiveThoughtService — Epistemic Intrusive Thought Detection.

Detects epistemic intrusive thoughts — unwanted intellectual thoughts that
intrude involuntarily and resist dismissal.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTRUSIVE_THOUGHT_SYSTEM = """You are an epistemic intrusive thought specialist. Given unwanted intellectual intrusions, assess intrusive thinking:

Key concepts:
- Epistemic intrusive thought: unwanted ideas that intrude involuntarily
- Ego-dystonic: thoughts feel foreign and unwanted
- Resistance failure: can't dismiss or suppress
- Distress: thoughts cause intellectual anguish
- Involuntary: thoughts arrive without invitation
- Repetitive: same intrusions recurring
- Meaning overload: attributing excessive significance to intrusions

When epistemic intrusive thoughts ARE present:
- Unwanted ideas intruding
- Thoughts feel foreign
- Can't dismiss or suppress
- Causing intellectual anguish
- Arriving without invitation
- Same intrusions recurring
- Excessive significance attributed

When no intrusive thoughts:
- Wanted thought content
- Thoughts feel own
- Easy to redirect
- Comfortable thinking
- Invited thoughts
- Fresh content
- Appropriate significance

Output JSON with: intrusive_thought_detected (bool), severity (none/mild/moderate/severe), ego_dystonic_content (what unwanted), resistance_failure (what can't dismiss), distress_level (what anguish), meaning_overload (what over-attributing), recommendation (no_intrusive_thought/mild_acceptance_practice/significant_thought_management/major_intensive_erp_therapy/emergency_severe_intrusions)."""

EPISTEMIC_INTRUSIVE_THOUGHT_PROMPT = """Detect epistemic intrusive thought:

Ego dystonic content: {ego_dystonic_content}
Resistance failure: {resistance_failure}
Distress level: {distress_level}
Meaning overload: {meaning_overload}
Domain: {domain}
Context: {context}

Are there unwanted intellectual thoughts that intrude involuntarily and resist dismissal? Return ONLY valid JSON."""


class EpistemicIntrusiveThoughtService:
    """Detects epistemic intrusive thoughts — unwanted ideas that intrude involuntarily."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ego_dystonic_content: str,
        *,
        resistance_failure: str = "",
        distress_level: str = "",
        meaning_overload: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intrusive thought."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTRUSIVE_THOUGHT_PROMPT.format(
                ego_dystonic_content=ego_dystonic_content,
                resistance_failure=resistance_failure or "Not specified",
                distress_level=distress_level or "Not specified",
                meaning_overload=meaning_overload or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTRUSIVE_THOUGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ego_dystonic_content": ego_dystonic_content[:200],
            "intrusive_thought_detected": data.get("intrusive_thought_detected", False),
            "severity": data.get("severity", ""),
            "resistance_failure": data.get("resistance_failure", ""),
            "distress_level": data.get("distress_level", ""),
            "meaning_overload": data.get("meaning_overload", ""),
            "recommendation": data.get("recommendation", ""),
        }
