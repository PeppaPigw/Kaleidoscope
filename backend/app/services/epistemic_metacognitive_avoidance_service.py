"""EpistemicMetacognitiveAvoidanceService — Epistemic Metacognitive Avoidance Detection.

Detects epistemic metacognitive avoidance — avoiding metacognitive
reflection to prevent uncomfortable self-knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METACOGNITIVE_AVOIDANCE_SYSTEM = """You are an epistemic metacognitive avoidance specialist. Given avoiding metacognitive reflection, assess metacognitive avoidance:

Key concepts:
- Epistemic metacognitive avoidance: avoiding metacognitive reflection
- Self-examination avoidance: avoiding examining own thinking
- Reflection resistance: resisting reflection on own processes
- Uncomfortable truth avoidance: avoiding uncomfortable truths about own thinking
- Meta-level escape: escaping from meta-level examination
- Process scrutiny avoidance: avoiding scrutiny of own processes
- Self-knowledge resistance: resisting self-knowledge about cognition

When epistemic metacognitive avoidance IS present:
- Metacognitive reflection avoided
- Self-examination avoided
- Reflection resisted
- Uncomfortable truths avoided
- Meta-level escaped from
- Process scrutiny avoided
- Self-knowledge resisted

When no metacognitive avoidance:
- Metacognitive reflection embraced
- Self-examination welcomed
- Reflection engaged
- Uncomfortable truths faced
- Meta-level engaged
- Process scrutiny accepted
- Self-knowledge sought

Output JSON with: metacognitive_avoidance_detected (bool), severity (none/mild/moderate/severe), self_examination_avoidance (what self-examination avoided), reflection_resistance (what reflection resisted), uncomfortable_truth_avoidance (what uncomfortable truths avoided), process_scrutiny_avoidance (what process scrutiny avoided), recommendation (no_metacognitive_avoidance/mild_reflection_encouragement/significant_self_examination_recovery/major_intensive_metacognitive_engagement/emergency_complete_metacognitive_avoidance)."""

EPISTEMIC_METACOGNITIVE_AVOIDANCE_PROMPT = """Detect epistemic metacognitive avoidance:

Self-examination avoidance: {self_examination_avoidance}
Reflection resistance: {reflection_resistance}
Uncomfortable truth avoidance: {uncomfortable_truth_avoidance}
Process scrutiny avoidance: {process_scrutiny_avoidance}
Domain: {domain}
Context: {context}

Is metacognitive reflection being avoided? Return ONLY valid JSON."""


class EpistemicMetacognitiveAvoidanceService:
    """Detects epistemic metacognitive avoidance — avoiding reflection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_examination_avoidance: str,
        *,
        reflection_resistance: str = "",
        uncomfortable_truth_avoidance: str = "",
        process_scrutiny_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metacognitive avoidance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METACOGNITIVE_AVOIDANCE_PROMPT.format(
                self_examination_avoidance=self_examination_avoidance,
                reflection_resistance=reflection_resistance or "Not specified",
                uncomfortable_truth_avoidance=uncomfortable_truth_avoidance or "Not specified",
                process_scrutiny_avoidance=process_scrutiny_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METACOGNITIVE_AVOIDANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_examination_avoidance": self_examination_avoidance[:200],
            "metacognitive_avoidance_detected": data.get("metacognitive_avoidance_detected", False),
            "severity": data.get("severity", ""),
            "reflection_resistance": data.get("reflection_resistance", ""),
            "uncomfortable_truth_avoidance": data.get("uncomfortable_truth_avoidance", ""),
            "process_scrutiny_avoidance": data.get("process_scrutiny_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
