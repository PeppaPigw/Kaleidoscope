"""EpistemicMetacognitiveBlindnessService — Epistemic Metacognitive Blindness Detection.

Detects epistemic metacognitive blindness — inability to see one's own
cognitive processes and how they shape conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METACOGNITIVE_BLINDNESS_SYSTEM = """You are an epistemic metacognitive blindness specialist. Given inability to see own cognitive processes, assess metacognitive blindness:

Key concepts:
- Epistemic metacognitive blindness: inability to see own cognitive processes
- Process invisibility: own thinking processes invisible to self
- Bias blindness: blind to own biases
- Strategy unawareness: unaware of own cognitive strategies
- Assumption invisibility: own assumptions invisible
- Pattern blindness: blind to own thinking patterns
- Influence unawareness: unaware of what influences own thinking

When epistemic metacognitive blindness IS present:
- Own processes invisible
- Biases unseen
- Strategies unaware
- Assumptions invisible
- Patterns blind to
- Influences unaware of
- Thinking opaque to self

When no metacognitive blindness:
- Own processes visible
- Biases recognized
- Strategies conscious
- Assumptions visible
- Patterns recognized
- Influences acknowledged
- Thinking transparent to self

Output JSON with: metacognitive_blindness_detected (bool), severity (none/mild/moderate/severe), process_invisibility (what processes invisible), bias_blindness (what biases unseen), strategy_unawareness (what strategies unaware of), assumption_invisibility (what assumptions invisible), recommendation (no_metacognitive_blindness/mild_reflection_practice/significant_self_observation/major_intensive_metacognitive_development/emergency_complete_metacognitive_blindness)."""

EPISTEMIC_METACOGNITIVE_BLINDNESS_PROMPT = """Detect epistemic metacognitive blindness:

Process invisibility: {process_invisibility}
Bias blindness: {bias_blindness}
Strategy unawareness: {strategy_unawareness}
Assumption invisibility: {assumption_invisibility}
Domain: {domain}
Context: {context}

Is there inability to see own cognitive processes? Return ONLY valid JSON."""


class EpistemicMetacognitiveBlindnessService:
    """Detects epistemic metacognitive blindness — inability to see own processes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process_invisibility: str,
        *,
        bias_blindness: str = "",
        strategy_unawareness: str = "",
        assumption_invisibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metacognitive blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METACOGNITIVE_BLINDNESS_PROMPT.format(
                process_invisibility=process_invisibility,
                bias_blindness=bias_blindness or "Not specified",
                strategy_unawareness=strategy_unawareness or "Not specified",
                assumption_invisibility=assumption_invisibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METACOGNITIVE_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process_invisibility": process_invisibility[:200],
            "metacognitive_blindness_detected": data.get("metacognitive_blindness_detected", False),
            "severity": data.get("severity", ""),
            "bias_blindness": data.get("bias_blindness", ""),
            "strategy_unawareness": data.get("strategy_unawareness", ""),
            "assumption_invisibility": data.get("assumption_invisibility", ""),
            "recommendation": data.get("recommendation", ""),
        }
