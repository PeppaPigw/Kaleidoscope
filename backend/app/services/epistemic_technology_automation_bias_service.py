"""EpistemicTechnologyAutomationBiasService — Epistemic Technology Automation Bias Detection.

Detects epistemic technology automation bias — humans over-trusting
automated systems.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECHNOLOGY_AUTOMATION_BIAS_SYSTEM = """You are an epistemic technology automation bias specialist. Given machine deference, assess human over-trust of automated systems:

Key concepts:
- Automation bias: humans over-trusting automated systems
- Machine deference: accepting automated outputs over human judgment
- Alert fatigue: repeated system prompts dulling critical attention
- Skill atrophy: human judgment weakening from disuse
- Human override reluctance: hesitation to challenge the machine

When automation bias IS present:
- Machine outputs are accepted without scrutiny
- Alerts are ignored or mechanically followed
- Human skill deteriorates
- Overrides feel illegitimate or risky
- Errors persist because the system appears authoritative

When no automation bias:
- Automated outputs are checked against evidence
- Alerts are interpreted critically
- Human expertise remains practiced
- Overrides are available and legitimate
- System confidence is calibrated

Output JSON with: automation_bias_detected (bool), severity (none/mild/moderate/severe), alert_fatigue (what alert fatigue appears), skill_atrophy (what skills are weakening), human_override_reluctance (what override reluctance exists), recommendation (no_automation_bias/mild_calibration/significant_human_review/major_skill_rebuilding/emergency_override_restoration)."""

EPISTEMIC_TECHNOLOGY_AUTOMATION_BIAS_PROMPT = """Detect epistemic technology automation bias:

Machine deference: {machine_deference}
Alert fatigue: {alert_fatigue}
Skill atrophy: {skill_atrophy}
Human override reluctance: {human_override_reluctance}
Domain: {domain}
Context: {context}

Are humans over-trusting automated systems? Return ONLY valid JSON."""


class EpistemicTechnologyAutomationBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        machine_deference: str,
        *,
        alert_fatigue: str = "",
        skill_atrophy: str = "",
        human_override_reluctance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECHNOLOGY_AUTOMATION_BIAS_PROMPT.format(
                machine_deference=machine_deference,
                alert_fatigue=alert_fatigue or "Not specified",
                skill_atrophy=skill_atrophy or "Not specified",
                human_override_reluctance=human_override_reluctance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECHNOLOGY_AUTOMATION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "machine_deference": machine_deference[:200],
            "automation_bias_detected": data.get("automation_bias_detected", False),
            "severity": data.get("severity", ""),
            "alert_fatigue": data.get("alert_fatigue", ""),
            "skill_atrophy": data.get("skill_atrophy", ""),
            "human_override_reluctance": data.get("human_override_reluctance", ""),
            "recommendation": data.get("recommendation", ""),
        }
