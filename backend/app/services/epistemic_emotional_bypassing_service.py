"""EpistemicEmotionalBypassingService — Epistemic Emotional Bypassing Detection.

Detects epistemic emotional bypassing — using intellectualization to
bypass emotional processing that is needed for full understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EMOTIONAL_BYPASSING_SYSTEM = """You are an epistemic emotional bypassing specialist. Given using intellectualization to bypass emotions, assess emotional bypassing:

Key concepts:
- Epistemic emotional bypassing: using intellectualization to bypass emotional processing
- Premature abstraction: abstracting before processing emotionally
- Intellectual escape: escaping into intellect to avoid feeling
- Analysis as avoidance: using analysis to avoid emotional engagement
- Conceptual distancing: using concepts to distance from feelings
- Theory as defense: using theory as defense against emotion
- Understanding without feeling: understanding intellectually without feeling

When epistemic emotional bypassing IS present:
- Using intellectualization to bypass
- Abstracting before processing
- Escaping into intellect
- Using analysis to avoid
- Using concepts to distance
- Using theory as defense
- Understanding without feeling

When no emotional bypassing:
- Integrating intellect and emotion
- Processing before abstracting
- Staying with feelings
- Analysis includes emotion
- Concepts include feeling
- Theory includes experience
- Understanding with feeling

Output JSON with: emotional_bypassing_detected (bool), severity (none/mild/moderate/severe), premature_abstraction (what abstracted before processing), intellectual_escape (what escaping from into intellect), analysis_as_avoidance (what using analysis to avoid), conceptual_distancing (what distancing from with concepts), recommendation (no_emotional_bypassing/mild_integration_practice/significant_feeling_engagement/major_intensive_emotional_processing/emergency_complete_emotional_bypassing)."""

EPISTEMIC_EMOTIONAL_BYPASSING_PROMPT = """Detect epistemic emotional bypassing:

Premature abstraction: {premature_abstraction}
Intellectual escape: {intellectual_escape}
Analysis as avoidance: {analysis_as_avoidance}
Conceptual distancing: {conceptual_distancing}
Domain: {domain}
Context: {context}

Is there using intellectualization to bypass emotional processing? Return ONLY valid JSON."""


class EpistemicEmotionalBypassingService:
    """Detects epistemic emotional bypassing — intellectualization bypassing emotions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_abstraction: str,
        *,
        intellectual_escape: str = "",
        analysis_as_avoidance: str = "",
        conceptual_distancing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic emotional bypassing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EMOTIONAL_BYPASSING_PROMPT.format(
                premature_abstraction=premature_abstraction,
                intellectual_escape=intellectual_escape or "Not specified",
                analysis_as_avoidance=analysis_as_avoidance or "Not specified",
                conceptual_distancing=conceptual_distancing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EMOTIONAL_BYPASSING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_abstraction": premature_abstraction[:200],
            "emotional_bypassing_detected": data.get("emotional_bypassing_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_escape": data.get("intellectual_escape", ""),
            "analysis_as_avoidance": data.get("analysis_as_avoidance", ""),
            "conceptual_distancing": data.get("conceptual_distancing", ""),
            "recommendation": data.get("recommendation", ""),
        }
