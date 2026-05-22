"""EpistemicSomnambulismService — Epistemic Somnambulism Detection.

Detects epistemic somnambulism — intellectual sleepwalking where complex
intellectual activities are performed without conscious awareness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOMNAMBULISM_SYSTEM = """You are an epistemic somnambulism specialist. Given intellectual sleepwalking, assess somnambulism patterns:

Key concepts:
- Epistemic somnambulism: performing intellectual work without awareness
- Automatism: complex intellectual behavior without consciousness
- Amnesia: no memory of intellectual activities performed
- Confusional arousal: disoriented intellectual state
- Sleep inertia: difficulty transitioning to full awareness
- Trigger: stress or deprivation precipitating episodes
- Safety concern: intellectual decisions made while unaware

When epistemic somnambulism IS present:
- Performing work without awareness
- Complex behavior without consciousness
- No memory of activities
- Disoriented intellectual state
- Difficulty reaching full awareness
- Stress precipitating episodes
- Decisions made while unaware

When no somnambulism:
- Full awareness during work
- Conscious intellectual behavior
- Complete memory of activities
- Oriented intellectual state
- Clear awareness transitions
- No stress-triggered episodes
- Decisions made consciously

Output JSON with: somnambulism_detected (bool), severity (none/mild/moderate/severe), automatism_type (what unconscious behavior), amnesia_extent (what memory gaps), trigger_pattern (what precipitates), safety_risk (what unaware decisions), recommendation (no_somnambulism/mild_sleep_hygiene/significant_scheduled_awakening/major_medication/emergency_dangerous_behavior)."""

EPISTEMIC_SOMNAMBULISM_PROMPT = """Detect epistemic somnambulism:

Automatism type: {automatism_type}
Amnesia extent: {amnesia_extent}
Trigger pattern: {trigger_pattern}
Safety risk: {safety_risk}
Domain: {domain}
Context: {context}

Are complex intellectual activities being performed without conscious awareness? Return ONLY valid JSON."""


class EpistemicSomnambulismService:
    """Detects epistemic somnambulism — intellectual sleepwalking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        automatism_type: str,
        *,
        amnesia_extent: str = "",
        trigger_pattern: str = "",
        safety_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic somnambulism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOMNAMBULISM_PROMPT.format(
                automatism_type=automatism_type,
                amnesia_extent=amnesia_extent or "Not specified",
                trigger_pattern=trigger_pattern or "Not specified",
                safety_risk=safety_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOMNAMBULISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "automatism_type": automatism_type[:200],
            "somnambulism_detected": data.get("somnambulism_detected", False),
            "severity": data.get("severity", ""),
            "amnesia_extent": data.get("amnesia_extent", ""),
            "trigger_pattern": data.get("trigger_pattern", ""),
            "safety_risk": data.get("safety_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
