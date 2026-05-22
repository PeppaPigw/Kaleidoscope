"""EpistemicCortisolExcessService — Epistemic Cortisol Excess Detection.

Detects epistemic cortisol excess — chronic stress hormone flooding
intellectual space, suppressing growth and repair.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CORTISOL_EXCESS_SYSTEM = """You are an epistemic cortisol excess specialist. Given chronic intellectual stress flooding, assess cortisol excess:

Key concepts:
- Epistemic cortisol excess: chronic stress flooding intellectual space
- Growth suppression: stress preventing intellectual development
- Immune suppression: stress weakening intellectual defenses
- Muscle wasting: stress consuming intellectual structure
- Central obesity: stress causing unhealthy accumulation
- HPA axis dysregulation: feedback loop broken
- Cushing syndrome: full manifestation of excess

When epistemic cortisol excess IS present:
- Chronic stress flooding intellectual space
- Growth and development suppressed
- Intellectual defenses weakened
- Intellectual structure being consumed
- Unhealthy accumulation occurring
- Feedback loop broken
- Full manifestation of excess present

When no cortisol excess:
- Normal stress levels
- Growth proceeding normally
- Defenses intact
- Structure maintained
- No unhealthy accumulation
- Feedback loop functioning
- No excess manifestation

Output JSON with: cortisol_excess_detected (bool), severity (none/mild/moderate/severe), stress_level (what flooding), growth_suppression (what development blocked), defense_status (what immune state), feedback_loop (what HPA axis), recommendation (no_excess/mild_stress_reduction/significant_cortisol_modulation/major_source_removal/emergency_adrenal_crisis)."""

EPISTEMIC_CORTISOL_EXCESS_PROMPT = """Detect epistemic cortisol excess:

Stress level: {stress_level}
Growth suppression: {growth_suppression}
Defense status: {defense_status}
Feedback loop: {feedback_loop}
Domain: {domain}
Context: {context}

Is chronic stress hormone flooding intellectual space suppressing growth and repair? Return ONLY valid JSON."""


class EpistemicCortisolExcessService:
    """Detects epistemic cortisol excess — chronic stress suppressing growth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stress_level: str,
        *,
        growth_suppression: str = "",
        defense_status: str = "",
        feedback_loop: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cortisol excess."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CORTISOL_EXCESS_PROMPT.format(
                stress_level=stress_level,
                growth_suppression=growth_suppression or "Not specified",
                defense_status=defense_status or "Not specified",
                feedback_loop=feedback_loop or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CORTISOL_EXCESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stress_level": stress_level[:200],
            "cortisol_excess_detected": data.get("cortisol_excess_detected", False),
            "severity": data.get("severity", ""),
            "growth_suppression": data.get("growth_suppression", ""),
            "defense_status": data.get("defense_status", ""),
            "feedback_loop": data.get("feedback_loop", ""),
            "recommendation": data.get("recommendation", ""),
        }
