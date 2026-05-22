"""EpistemicMetacognitiveRigidityService — Epistemic Metacognitive Rigidity Detection.

Detects epistemic metacognitive rigidity — rigid metacognitive strategies
that don't adapt to different epistemic situations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METACOGNITIVE_RIGIDITY_SYSTEM = """You are an epistemic metacognitive rigidity specialist. Given rigid metacognitive strategies that don't adapt, assess metacognitive rigidity:

Key concepts:
- Epistemic metacognitive rigidity: rigid strategies that don't adapt
- Strategy fixation: fixated on one metacognitive strategy
- Approach inflexibility: inflexible in approach to thinking about thinking
- One-size-fits-all: applying same meta-strategy to all situations
- Adaptation failure: failing to adapt metacognitive approach
- Context insensitivity: insensitive to context in metacognition
- Method ossification: metacognitive methods ossified

When epistemic metacognitive rigidity IS present:
- Strategies rigid and unadapting
- Fixated on one strategy
- Approach inflexible
- One-size-fits-all applied
- Adaptation failing
- Context insensitive
- Methods ossified

When no metacognitive rigidity:
- Strategies flexible and adaptive
- Multiple strategies available
- Approach flexible
- Context-appropriate strategies
- Adaptation successful
- Context sensitive
- Methods evolving

Output JSON with: metacognitive_rigidity_detected (bool), severity (none/mild/moderate/severe), strategy_fixation (what strategy fixated on), approach_inflexibility (what approach inflexible about), adaptation_failure (what failing to adapt to), context_insensitivity (what context insensitive to), recommendation (no_metacognitive_rigidity/mild_flexibility_practice/significant_strategy_diversification/major_intensive_adaptation_recovery/emergency_complete_metacognitive_rigidity)."""

EPISTEMIC_METACOGNITIVE_RIGIDITY_PROMPT = """Detect epistemic metacognitive rigidity:

Strategy fixation: {strategy_fixation}
Approach inflexibility: {approach_inflexibility}
Adaptation failure: {adaptation_failure}
Context insensitivity: {context_insensitivity}
Domain: {domain}
Context: {context}

Are metacognitive strategies rigid and failing to adapt? Return ONLY valid JSON."""


class EpistemicMetacognitiveRigidityService:
    """Detects epistemic metacognitive rigidity — rigid unadapting strategies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategy_fixation: str,
        *,
        approach_inflexibility: str = "",
        adaptation_failure: str = "",
        context_insensitivity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metacognitive rigidity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METACOGNITIVE_RIGIDITY_PROMPT.format(
                strategy_fixation=strategy_fixation,
                approach_inflexibility=approach_inflexibility or "Not specified",
                adaptation_failure=adaptation_failure or "Not specified",
                context_insensitivity=context_insensitivity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METACOGNITIVE_RIGIDITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategy_fixation": strategy_fixation[:200],
            "metacognitive_rigidity_detected": data.get("metacognitive_rigidity_detected", False),
            "severity": data.get("severity", ""),
            "approach_inflexibility": data.get("approach_inflexibility", ""),
            "adaptation_failure": data.get("adaptation_failure", ""),
            "context_insensitivity": data.get("context_insensitivity", ""),
            "recommendation": data.get("recommendation", ""),
        }
