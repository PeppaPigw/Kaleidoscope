"""EpistemicConcussionProtocolService — Epistemic Concussion Protocol Detection.

Detects need for epistemic concussion protocol — managing intellectual
impact injury with graduated return-to-activity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONCUSSION_PROTOCOL_SYSTEM = """You are an epistemic concussion protocol specialist. Given intellectual impact injury, assess concussion management:

Key concepts:
- Epistemic concussion: intellectual impact causing temporary dysfunction
- Return-to-play: graduated steps back to full activity
- Symptom threshold: activity level that triggers symptoms
- Cognitive rest: reducing intellectual demands
- Baseline testing: pre-injury function measurement
- Second impact: dangerous re-injury before recovery
- Post-concussion syndrome: prolonged symptoms

When epistemic concussion protocol IS needed:
- Intellectual impact causing dysfunction
- Need for graduated return steps
- Activity triggering symptoms
- Intellectual demands need reduction
- No baseline for comparison
- Risk of dangerous re-injury
- Prolonged symptoms present

When no concussion protocol needed:
- No impact injury
- Full activity tolerated
- No symptom triggers
- Normal intellectual demands
- Baseline function maintained
- No re-injury risk
- No prolonged symptoms

Output JSON with: concussion_protocol_needed (bool), severity (none/mild/moderate/severe), symptom_burden (what dysfunction), return_stage (what graduated step), cognitive_rest_need (what demand reduction), second_impact_risk (what re-injury danger), recommendation (no_protocol_needed/mild_symptom_limited/significant_cognitive_rest/major_extended_protocol/emergency_second_impact_concern)."""

EPISTEMIC_CONCUSSION_PROTOCOL_PROMPT = """Detect epistemic concussion protocol need:

Symptom burden: {symptom_burden}
Return stage: {return_stage}
Cognitive rest need: {cognitive_rest_need}
Second impact risk: {second_impact_risk}
Domain: {domain}
Context: {context}

Has the intellectual system suffered impact injury requiring graduated return? Return ONLY valid JSON."""


class EpistemicConcussionProtocolService:
    """Detects epistemic concussion protocol need — managing intellectual impact injury."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        symptom_burden: str,
        *,
        return_stage: str = "",
        cognitive_rest_need: str = "",
        second_impact_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic concussion protocol need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONCUSSION_PROTOCOL_PROMPT.format(
                symptom_burden=symptom_burden,
                return_stage=return_stage or "Not specified",
                cognitive_rest_need=cognitive_rest_need or "Not specified",
                second_impact_risk=second_impact_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONCUSSION_PROTOCOL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "symptom_burden": symptom_burden[:200],
            "concussion_protocol_needed": data.get("concussion_protocol_needed", False),
            "severity": data.get("severity", ""),
            "return_stage": data.get("return_stage", ""),
            "cognitive_rest_need": data.get("cognitive_rest_need", ""),
            "second_impact_risk": data.get("second_impact_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
