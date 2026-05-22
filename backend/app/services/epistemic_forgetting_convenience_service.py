"""EpistemicForgettingConvenienceService — Epistemic Forgetting Convenience Detection.

Detects epistemic forgetting convenience — conveniently forgetting
information that contradicts current position or narrative.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FORGETTING_CONVENIENCE_SYSTEM = """You are an epistemic forgetting convenience specialist. Given conveniently forgetting contradicting info, assess forgetting convenience:

Key concepts:
- Epistemic forgetting convenience: conveniently forgetting contradicting information
- Strategic amnesia: forgetting strategically what contradicts position
- Inconvenient fact erasure: erasing inconvenient facts from memory
- Contradiction suppression: suppressing memories of contradictions
- Position-threatening forgetting: forgetting what threatens position
- Accountability avoidance: forgetting to avoid accountability
- Commitment erasure: erasing memory of past commitments

When epistemic forgetting convenience IS present:
- Conveniently forgetting contradicting info
- Strategically forgetting
- Erasing inconvenient facts
- Suppressing contradiction memories
- Forgetting position-threatening info
- Forgetting to avoid accountability
- Erasing past commitments

When no forgetting convenience:
- Retaining all relevant info
- Honest memory
- Retaining inconvenient facts
- Acknowledging contradictions
- Remembering threatening info
- Maintaining accountability
- Honoring past commitments

Output JSON with: forgetting_convenience_detected (bool), severity (none/mild/moderate/severe), strategic_amnesia (what strategically forgotten), inconvenient_fact_erasure (what facts erased), contradiction_suppression (what contradictions suppressed), accountability_avoidance (what accountability avoided through forgetting), recommendation (no_forgetting_convenience/mild_honesty_practice/significant_memory_integrity/major_intensive_accountability/emergency_complete_strategic_forgetting)."""

EPISTEMIC_FORGETTING_CONVENIENCE_PROMPT = """Detect epistemic forgetting convenience:

Strategic amnesia: {strategic_amnesia}
Inconvenient fact erasure: {inconvenient_fact_erasure}
Contradiction suppression: {contradiction_suppression}
Accountability avoidance: {accountability_avoidance}
Domain: {domain}
Context: {context}

Is there conveniently forgetting information that contradicts current position? Return ONLY valid JSON."""


class EpistemicForgettingConvenienceService:
    """Detects epistemic forgetting convenience — conveniently forgetting contradictions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategic_amnesia: str,
        *,
        inconvenient_fact_erasure: str = "",
        contradiction_suppression: str = "",
        accountability_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic forgetting convenience."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FORGETTING_CONVENIENCE_PROMPT.format(
                strategic_amnesia=strategic_amnesia,
                inconvenient_fact_erasure=inconvenient_fact_erasure or "Not specified",
                contradiction_suppression=contradiction_suppression or "Not specified",
                accountability_avoidance=accountability_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FORGETTING_CONVENIENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategic_amnesia": strategic_amnesia[:200],
            "forgetting_convenience_detected": data.get("forgetting_convenience_detected", False),
            "severity": data.get("severity", ""),
            "inconvenient_fact_erasure": data.get("inconvenient_fact_erasure", ""),
            "contradiction_suppression": data.get("contradiction_suppression", ""),
            "accountability_avoidance": data.get("accountability_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
