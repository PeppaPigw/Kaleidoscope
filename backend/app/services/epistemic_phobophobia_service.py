"""EpistemicPhobophobiaService — Epistemic Phobophobia Detection.

Detects epistemic phobophobia — fear of intellectual fear itself,
meta-anxiety about experiencing cognitive anxiety.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHOBOPHOBIA_SYSTEM = """You are an epistemic phobophobia specialist. Given fear of intellectual fear, assess phobophobia:

Key concepts:
- Epistemic phobophobia: fear of intellectual fear itself
- Meta-anxiety: anxiety about experiencing anxiety
- Fear of fear: dreading the experience of intellectual distress
- Hypervigilance: constantly monitoring for signs of fear
- Avoidance of avoidance: avoiding situations that might trigger fear
- Catastrophizing: believing fear itself will be unbearable
- Self-fulfilling: fear of fear creating the feared state

When epistemic phobophobia IS present:
- Fear of intellectual fear itself
- Anxiety about experiencing anxiety
- Dreading intellectual distress
- Monitoring for fear signs
- Avoiding potential triggers
- Believing fear unbearable
- Creating feared state

When no phobophobia:
- Accepting intellectual discomfort
- No meta-anxiety
- Tolerating distress
- Not monitoring for fear
- Engaging despite risk
- Knowing fear is manageable
- No self-fulfilling cycle

Output JSON with: phobophobia_detected (bool), severity (none/mild/moderate/severe), meta_anxiety_level (what fear of fear), hypervigilance_pattern (what monitoring), catastrophizing_level (what unbearability belief), self_fulfilling_cycle (what creation of feared state), recommendation (no_phobophobia/mild_acceptance_practice/significant_metacognitive_therapy/major_intensive_intervention/emergency_complete_paralysis)."""

EPISTEMIC_PHOBOPHOBIA_PROMPT = """Detect epistemic phobophobia:

Meta anxiety level: {meta_anxiety_level}
Hypervigilance pattern: {hypervigilance_pattern}
Catastrophizing level: {catastrophizing_level}
Self fulfilling cycle: {self_fulfilling_cycle}
Domain: {domain}
Context: {context}

Is there fear of intellectual fear itself — meta-anxiety about cognitive anxiety? Return ONLY valid JSON."""


class EpistemicPhobophobiaService:
    """Detects epistemic phobophobia — fear of intellectual fear itself."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meta_anxiety_level: str,
        *,
        hypervigilance_pattern: str = "",
        catastrophizing_level: str = "",
        self_fulfilling_cycle: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic phobophobia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHOBOPHOBIA_PROMPT.format(
                meta_anxiety_level=meta_anxiety_level,
                hypervigilance_pattern=hypervigilance_pattern or "Not specified",
                catastrophizing_level=catastrophizing_level or "Not specified",
                self_fulfilling_cycle=self_fulfilling_cycle or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHOBOPHOBIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meta_anxiety_level": meta_anxiety_level[:200],
            "phobophobia_detected": data.get("phobophobia_detected", False),
            "severity": data.get("severity", ""),
            "hypervigilance_pattern": data.get("hypervigilance_pattern", ""),
            "catastrophizing_level": data.get("catastrophizing_level", ""),
            "self_fulfilling_cycle": data.get("self_fulfilling_cycle", ""),
            "recommendation": data.get("recommendation", ""),
        }
