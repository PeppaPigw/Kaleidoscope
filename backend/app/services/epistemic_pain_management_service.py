"""EpistemicPainManagementService — Epistemic Pain Management Detection.

Detects epistemic pain management need — controlling intellectual suffering
through multimodal approaches.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PAIN_MANAGEMENT_SYSTEM = """You are an epistemic pain management specialist. Given intellectual suffering, assess pain management need:

Key concepts:
- Epistemic pain management: controlling intellectual suffering
- Acute pain: sudden onset intellectual distress
- Chronic pain: persistent ongoing suffering
- Nociceptive: pain from actual intellectual damage
- Neuropathic: pain from nerve pathway dysfunction
- Multimodal: combining multiple approaches
- Pain ladder: escalating interventions by severity

When epistemic pain management IS needed:
- Intellectual suffering present
- Sudden onset distress occurring
- Persistent ongoing suffering
- Actual damage causing pain
- Pathway dysfunction causing pain
- Multiple approaches needed
- Escalating interventions required

When no pain management needed:
- No intellectual suffering
- No distress present
- No ongoing pain
- No damage-related pain
- No pathway dysfunction
- Single approach sufficient
- No escalation needed

Output JSON with: pain_management_needed (bool), severity (none/mild/moderate/severe), pain_type (what category), pain_source (what origin), current_control (what existing management), escalation_need (what next step), recommendation (no_pain_management_needed/mild_non_pharmacological/significant_moderate_intervention/major_multimodal/emergency_acute_pain_crisis)."""

EPISTEMIC_PAIN_MANAGEMENT_PROMPT = """Detect epistemic pain management need:

Pain type: {pain_type}
Pain source: {pain_source}
Current control: {current_control}
Escalation need: {escalation_need}
Domain: {domain}
Context: {context}

Is intellectual suffering present requiring pain management? Return ONLY valid JSON."""


class EpistemicPainManagementService:
    """Detects epistemic pain management need — controlling intellectual suffering."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pain_type: str,
        *,
        pain_source: str = "",
        current_control: str = "",
        escalation_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pain management need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PAIN_MANAGEMENT_PROMPT.format(
                pain_type=pain_type,
                pain_source=pain_source or "Not specified",
                current_control=current_control or "Not specified",
                escalation_need=escalation_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PAIN_MANAGEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pain_type": pain_type[:200],
            "pain_management_needed": data.get("pain_management_needed", False),
            "severity": data.get("severity", ""),
            "pain_source": data.get("pain_source", ""),
            "current_control": data.get("current_control", ""),
            "escalation_need": data.get("escalation_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
