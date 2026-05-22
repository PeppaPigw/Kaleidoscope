"""EpistemicBruxismService — Epistemic Bruxism Detection.

Detects epistemic bruxism — unconscious grinding of intellectual concepts
against each other, causing wear and damage.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRUXISM_SYSTEM = """You are an epistemic bruxism specialist. Given unconscious intellectual grinding, assess bruxism:

Key concepts:
- Epistemic bruxism: unconscious grinding of concepts
- Clenching: sustained pressure between opposing ideas
- Attrition: wear from concept-on-concept contact
- Night guard: protective barrier during unconscious periods
- TMJ pain: joint dysfunction from grinding
- Stress-related: grinding triggered by intellectual tension
- Tooth fracture: concept breaking from grinding force

When epistemic bruxism IS present:
- Unconscious grinding of concepts
- Sustained pressure between opposing ideas
- Wear from repeated contact
- No protective barrier present
- Joint dysfunction from grinding
- Triggered by intellectual tension
- Concepts breaking from force

When no bruxism:
- No unconscious grinding
- Normal pressure between ideas
- No abnormal wear
- Protective barriers in place
- Normal joint function
- No tension-triggered grinding
- Concepts intact

Output JSON with: bruxism_detected (bool), severity (none/mild/moderate/severe), grinding_pattern (what contact), wear_extent (what damage), stress_trigger (what tension), protection_status (what barrier), recommendation (no_bruxism/mild_awareness/significant_night_guard/major_comprehensive_treatment/emergency_acute_fracture)."""

EPISTEMIC_BRUXISM_PROMPT = """Detect epistemic bruxism:

Grinding pattern: {grinding_pattern}
Wear extent: {wear_extent}
Stress trigger: {stress_trigger}
Protection status: {protection_status}
Domain: {domain}
Context: {context}

Are intellectual concepts being unconsciously ground against each other? Return ONLY valid JSON."""


class EpistemicBruxismService:
    """Detects epistemic bruxism — unconscious grinding of concepts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        grinding_pattern: str,
        *,
        wear_extent: str = "",
        stress_trigger: str = "",
        protection_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bruxism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRUXISM_PROMPT.format(
                grinding_pattern=grinding_pattern,
                wear_extent=wear_extent or "Not specified",
                stress_trigger=stress_trigger or "Not specified",
                protection_status=protection_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRUXISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "grinding_pattern": grinding_pattern[:200],
            "bruxism_detected": data.get("bruxism_detected", False),
            "severity": data.get("severity", ""),
            "wear_extent": data.get("wear_extent", ""),
            "stress_trigger": data.get("stress_trigger", ""),
            "protection_status": data.get("protection_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
