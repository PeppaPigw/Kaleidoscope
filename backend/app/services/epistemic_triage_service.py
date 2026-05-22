"""EpistemicTriageService — Epistemic Triage Detection.

Detects need for epistemic triage — prioritizing which intellectual injuries
need immediate attention based on severity and salvageability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRIAGE_SYSTEM = """You are an epistemic triage specialist. Given multiple intellectual injuries, assess prioritization needs:

Key concepts:
- Epistemic triage: prioritizing intellectual injuries by urgency
- Immediate: life-threatening, salvageable with prompt action
- Delayed: serious but can wait without deterioration
- Minor: walking wounded, minimal intervention needed
- Expectant: too far gone to save with available resources
- Overtriage: treating minor as critical (wastes resources)
- Undertriage: treating critical as minor (causes death)

When epistemic triage IS needed:
- Multiple intellectual injuries competing for attention
- Life-threatening salvageable conditions present
- Serious conditions that can safely wait
- Minor conditions requiring minimal intervention
- Conditions too far gone to save
- Risk of overtriage wasting resources
- Risk of undertriage causing intellectual death

When no triage needed:
- Single clear priority
- No competing demands
- All conditions stable
- No life-threatening issues
- No resource constraints
- No prioritization needed
- Adequate capacity for all

Output JSON with: triage_needed (bool), severity (none/mild/moderate/severe), immediate_cases (what life-threatening salvageable), delayed_cases (what can wait), expectant_cases (what unsalvageable), undertriage_risk (what missed critical), recommendation (no_triage_needed/mild_prioritization/significant_triage/major_mass_casualty/implement_intellectual_triage_protocol)."""

EPISTEMIC_TRIAGE_PROMPT = """Detect epistemic triage need:

Immediate cases: {immediate_cases}
Delayed cases: {delayed_cases}
Expectant cases: {expectant_cases}
Undertriage risk: {undertriage_risk}
Domain: {domain}
Context: {context}

Do multiple intellectual injuries need prioritization for immediate attention? Return ONLY valid JSON."""


class EpistemicTriageService:
    """Detects epistemic triage need — prioritizing intellectual injuries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        immediate_cases: str,
        *,
        delayed_cases: str = "",
        expectant_cases: str = "",
        undertriage_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic triage need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRIAGE_PROMPT.format(
                immediate_cases=immediate_cases,
                delayed_cases=delayed_cases or "Not specified",
                expectant_cases=expectant_cases or "Not specified",
                undertriage_risk=undertriage_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRIAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "immediate_cases": immediate_cases[:200],
            "triage_needed": data.get("triage_needed", False),
            "severity": data.get("severity", ""),
            "delayed_cases": data.get("delayed_cases", ""),
            "expectant_cases": data.get("expectant_cases", ""),
            "undertriage_risk": data.get("undertriage_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
