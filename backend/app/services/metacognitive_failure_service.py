"""MetacognitiveFailureService — Metacognitive Failure Detection.

Detects metacognitive failure — failure to monitor one's own thinking
processes, not knowing what you don't know about your own cognition,
lacking awareness of cognitive limitations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

METACOGNITIVE_FAILURE_SYSTEM = """You are a metacognitive failure specialist. Given a cognitive performance or claim, assess whether metacognition is failing:

Key concepts:
- Metacognitive failure: not monitoring own thinking
- Calibration failure: confidence not matching accuracy
- Blind spot unawareness: not knowing about own blind spots
- Cognitive monitoring: tracking quality of own thinking
- Feeling of knowing: subjective sense vs. actual knowledge
- Judgment of learning: inaccurate assessment of own learning
- Metacognitive illusion: false sense of understanding

When metacognitive failure IS present:
- No monitoring of own thinking quality
- Confidence uncalibrated to actual performance
- Blind spots unrecognized
- Feeling of knowing disconnected from actual knowledge
- No checking of own reasoning
- Cognitive limitations unacknowledged
- False sense of understanding maintained

When metacognition is appropriate:
- Own thinking actively monitored
- Confidence calibrated to track record
- Known blind spots acknowledged
- Feeling of knowing tested against evidence
- Reasoning checked for errors
- Cognitive limitations recognized
- Understanding verified, not assumed

Output JSON with: failure_present (bool), severity (none/mild/moderate/severe), cognition (what cognitive process is involved), monitoring_gap (what monitoring is missing), calibration (how well-calibrated is confidence), blind_spots (what blind spots are unrecognized), recommendation (appropriate_metacognition/mild_monitoring_gap/significant_metacognitive_failure/major_calibration_failure/implement_cognitive_monitoring)."""

METACOGNITIVE_FAILURE_PROMPT = """Detect metacognitive failure:

Claim: {claim}
Confidence level: {confidence}
Track record: {track_record}
Self-awareness: {awareness}
Domain: {domain}
Context: {context}

Is there a failure to monitor one's own thinking processes? Return ONLY valid JSON."""


class MetacognitiveFailureService:
    """Detects metacognitive failure — failure to monitor own thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        confidence: str = "",
        track_record: str = "",
        awareness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect metacognitive failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=METACOGNITIVE_FAILURE_PROMPT.format(
                claim=claim,
                confidence=confidence or "Not specified",
                track_record=track_record or "Not specified",
                awareness=awareness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=METACOGNITIVE_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "failure_present": data.get("failure_present", False),
            "severity": data.get("severity", ""),
            "monitoring_gap": data.get("monitoring_gap", ""),
            "calibration": data.get("calibration", ""),
            "blind_spots": data.get("blind_spots", ""),
            "recommendation": data.get("recommendation", ""),
        }
