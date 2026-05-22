"""EpistemicProlongedGriefService — Epistemic Prolonged Grief Detection.

Detects epistemic prolonged grief — persistent intense longing for lost
intellectual framework or paradigm beyond normal adaptation period.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROLONGED_GRIEF_SYSTEM = """You are an epistemic prolonged grief specialist. Given persistent intellectual loss, assess prolonged grief:

Key concepts:
- Epistemic prolonged grief: persistent longing for lost framework
- Yearning: intense desire for return of lost paradigm
- Preoccupation: consumed by thoughts of what was lost
- Identity disruption: who am I without this framework
- Emotional numbness: inability to feel intellectual engagement
- Avoidance: steering away from reminders of loss
- Functional impairment: grief affecting intellectual performance

When epistemic prolonged grief IS present:
- Persistent longing for lost framework
- Intense desire for return
- Consumed by loss thoughts
- Identity disrupted
- Emotionally numb
- Avoiding reminders
- Performance impaired

When no prolonged grief:
- Adapted to loss
- Moved forward
- Thoughts manageable
- Identity intact
- Emotionally engaged
- Facing reminders
- Performance maintained

Output JSON with: prolonged_grief_detected (bool), severity (none/mild/moderate/severe), yearning_intensity (what longing), preoccupation_level (what consumed), identity_impact (what disruption), functional_impairment (what performance), recommendation (no_prolonged_grief/mild_grief_support/significant_grief_therapy/major_intensive_treatment/emergency_severe_impairment)."""

EPISTEMIC_PROLONGED_GRIEF_PROMPT = """Detect epistemic prolonged grief:

Yearning intensity: {yearning_intensity}
Preoccupation level: {preoccupation_level}
Identity impact: {identity_impact}
Functional impairment: {functional_impairment}
Domain: {domain}
Context: {context}

Is there persistent intense longing for lost intellectual framework beyond normal adaptation? Return ONLY valid JSON."""


class EpistemicProlongedGriefService:
    """Detects epistemic prolonged grief — persistent longing for lost framework."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        yearning_intensity: str,
        *,
        preoccupation_level: str = "",
        identity_impact: str = "",
        functional_impairment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prolonged grief."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROLONGED_GRIEF_PROMPT.format(
                yearning_intensity=yearning_intensity,
                preoccupation_level=preoccupation_level or "Not specified",
                identity_impact=identity_impact or "Not specified",
                functional_impairment=functional_impairment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROLONGED_GRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "yearning_intensity": yearning_intensity[:200],
            "prolonged_grief_detected": data.get("prolonged_grief_detected", False),
            "severity": data.get("severity", ""),
            "preoccupation_level": data.get("preoccupation_level", ""),
            "identity_impact": data.get("identity_impact", ""),
            "functional_impairment": data.get("functional_impairment", ""),
            "recommendation": data.get("recommendation", ""),
        }
