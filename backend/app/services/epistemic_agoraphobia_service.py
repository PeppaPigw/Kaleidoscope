"""EpistemicAgoraphobiaService — Epistemic Agoraphobia Detection.

Detects epistemic agoraphobia — fear of open intellectual spaces where
escape to familiar frameworks feels impossible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AGORAPHOBIA_SYSTEM = """You are an epistemic agoraphobia specialist. Given fear of open intellectual spaces, assess agoraphobia:

Key concepts:
- Epistemic agoraphobia: fear of open intellectual spaces
- Open spaces: unfamiliar intellectual territory without structure
- Escape difficulty: feeling trapped without familiar frameworks
- Panic: overwhelming anxiety in unstructured thinking
- Avoidance: refusing to enter unfamiliar intellectual territory
- Safety behaviors: only thinking within known boundaries
- Anticipatory anxiety: dreading future intellectual openness

When epistemic agoraphobia IS present:
- Fear of open intellectual spaces
- Unfamiliar territory overwhelming
- Feeling trapped without frameworks
- Panic in unstructured thinking
- Refusing unfamiliar territory
- Only thinking within boundaries
- Dreading future openness

When no agoraphobia:
- Comfortable in open spaces
- Exploring unfamiliar territory
- Flexible framework use
- Calm in unstructured thinking
- Entering new territory
- Thinking beyond boundaries
- Anticipating exploration

Output JSON with: agoraphobia_detected (bool), severity (none/mild/moderate/severe), open_space_fear (what territory avoidance), escape_need (what framework dependence), panic_pattern (what overwhelm), avoidance_scope (what restriction), recommendation (no_agoraphobia/mild_gradual_exposure/significant_systematic_desensitization/major_intensive_therapy/emergency_complete_avoidance)."""

EPISTEMIC_AGORAPHOBIA_PROMPT = """Detect epistemic agoraphobia:

Open space fear: {open_space_fear}
Escape need: {escape_need}
Panic pattern: {panic_pattern}
Avoidance scope: {avoidance_scope}
Domain: {domain}
Context: {context}

Is there fear of open intellectual spaces where escape to familiar frameworks feels impossible? Return ONLY valid JSON."""


class EpistemicAgoraphobiaService:
    """Detects epistemic agoraphobia — fear of open intellectual spaces."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        open_space_fear: str,
        *,
        escape_need: str = "",
        panic_pattern: str = "",
        avoidance_scope: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic agoraphobia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AGORAPHOBIA_PROMPT.format(
                open_space_fear=open_space_fear,
                escape_need=escape_need or "Not specified",
                panic_pattern=panic_pattern or "Not specified",
                avoidance_scope=avoidance_scope or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AGORAPHOBIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "open_space_fear": open_space_fear[:200],
            "agoraphobia_detected": data.get("agoraphobia_detected", False),
            "severity": data.get("severity", ""),
            "escape_need": data.get("escape_need", ""),
            "panic_pattern": data.get("panic_pattern", ""),
            "avoidance_scope": data.get("avoidance_scope", ""),
            "recommendation": data.get("recommendation", ""),
        }
