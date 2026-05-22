"""EpistemicCognitiveSolitudeService — Epistemic Cognitive Solitude Detection.

Detects epistemic cognitive solitude — forced solitude due to cognitive
differences that prevent meaningful intellectual connection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_SOLITUDE_SYSTEM = """You are an epistemic cognitive solitude specialist. Given forced solitude from cognitive differences, assess cognitive solitude:

Key concepts:
- Epistemic cognitive solitude: forced solitude from cognitive differences
- Processing mismatch: thinking differently from everyone around
- Speed isolation: processing faster or slower than peers
- Pattern recognition gap: seeing patterns others miss
- Associative distance: making connections others cannot follow
- Neurodivergent isolation: cognitive style creating distance
- Temporal mismatch: operating on different intellectual timescales

When epistemic cognitive solitude IS present:
- Forced solitude from cognitive differences
- Thinking differently from everyone
- Processing at different speed
- Seeing patterns others miss
- Making connections others cannot follow
- Cognitive style creating distance
- Operating on different timescales

When no cognitive solitude:
- Connected despite differences
- Thinking complementing others
- Processing speed matched
- Shared pattern recognition
- Connections followed by others
- Cognitive style appreciated
- Synchronized timescales

Output JSON with: cognitive_solitude_detected (bool), severity (none/mild/moderate/severe), processing_mismatch (what thinking differently), speed_isolation (what processing differently), pattern_recognition_gap (what seeing that others miss), associative_distance (what connections not followed), recommendation (no_cognitive_solitude/mild_adaptation_practice/significant_connection_seeking/major_intensive_belonging_work/emergency_severe_cognitive_isolation)."""

EPISTEMIC_COGNITIVE_SOLITUDE_PROMPT = """Detect epistemic cognitive solitude:

Processing mismatch: {processing_mismatch}
Speed isolation: {speed_isolation}
Pattern recognition gap: {pattern_recognition_gap}
Associative distance: {associative_distance}
Domain: {domain}
Context: {context}

Is there forced solitude due to cognitive differences? Return ONLY valid JSON."""


class EpistemicCognitiveSolitudeService:
    """Detects epistemic cognitive solitude — forced solitude from cognitive differences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        processing_mismatch: str,
        *,
        speed_isolation: str = "",
        pattern_recognition_gap: str = "",
        associative_distance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive solitude."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_SOLITUDE_PROMPT.format(
                processing_mismatch=processing_mismatch,
                speed_isolation=speed_isolation or "Not specified",
                pattern_recognition_gap=pattern_recognition_gap or "Not specified",
                associative_distance=associative_distance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_SOLITUDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "processing_mismatch": processing_mismatch[:200],
            "cognitive_solitude_detected": data.get("cognitive_solitude_detected", False),
            "severity": data.get("severity", ""),
            "speed_isolation": data.get("speed_isolation", ""),
            "pattern_recognition_gap": data.get("pattern_recognition_gap", ""),
            "associative_distance": data.get("associative_distance", ""),
            "recommendation": data.get("recommendation", ""),
        }
