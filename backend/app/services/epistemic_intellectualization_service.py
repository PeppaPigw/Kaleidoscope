"""EpistemicIntellectualizationService — Epistemic Intellectualization Detection.

Detects epistemic intellectualization — using abstract intellectual analysis
to avoid emotional engagement with threatening ideas or implications.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUALIZATION_SYSTEM = """You are an epistemic intellectualization specialist. Given abstract avoidance of emotional engagement, assess intellectualization:

Key concepts:
- Epistemic intellectualization: using abstraction to avoid emotion
- Emotional bypass: thinking about rather than feeling
- Detached analysis: treating personal threats as academic
- Jargon shield: technical language as emotional barrier
- Meta-level escape: discussing the discussion instead of engaging
- Premature theorizing: abstracting before understanding
- Affective avoidance: systematically avoiding emotional implications

When epistemic intellectualization IS present:
- Using abstraction to avoid
- Thinking instead of feeling
- Treating threats as academic
- Technical language as barrier
- Discussing discussion
- Abstracting before understanding
- Avoiding emotional implications

When no intellectualization:
- Integrated thinking-feeling
- Feeling and thinking together
- Engaging personally
- Language serves communication
- Direct engagement
- Understanding before abstracting
- Facing implications

Output JSON with: intellectualization_detected (bool), severity (none/mild/moderate/severe), emotional_bypass (what avoiding), detachment_pattern (what treating academic), jargon_shield (what barrier), meta_escape (what discussing discussion), recommendation (no_intellectualization/mild_emotional_integration/significant_affect_therapy/major_intensive_reconnection/emergency_complete_dissociation)."""

EPISTEMIC_INTELLECTUALIZATION_PROMPT = """Detect epistemic intellectualization:

Emotional bypass: {emotional_bypass}
Detachment pattern: {detachment_pattern}
Jargon shield: {jargon_shield}
Meta escape: {meta_escape}
Domain: {domain}
Context: {context}

Is there use of abstract analysis to avoid emotional engagement with threatening ideas? Return ONLY valid JSON."""


class EpistemicIntellectualizationService:
    """Detects epistemic intellectualization — abstraction to avoid emotion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        emotional_bypass: str,
        *,
        detachment_pattern: str = "",
        jargon_shield: str = "",
        meta_escape: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectualization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUALIZATION_PROMPT.format(
                emotional_bypass=emotional_bypass,
                detachment_pattern=detachment_pattern or "Not specified",
                jargon_shield=jargon_shield or "Not specified",
                meta_escape=meta_escape or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "emotional_bypass": emotional_bypass[:200],
            "intellectualization_detected": data.get("intellectualization_detected", False),
            "severity": data.get("severity", ""),
            "detachment_pattern": data.get("detachment_pattern", ""),
            "jargon_shield": data.get("jargon_shield", ""),
            "meta_escape": data.get("meta_escape", ""),
            "recommendation": data.get("recommendation", ""),
        }
