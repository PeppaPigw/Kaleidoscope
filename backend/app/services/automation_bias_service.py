"""AutomationBiasService — Automation Bias Detection.

Detects automation bias — over-reliance on automated systems,
accepting their output without sufficient critical evaluation.
Parasuraman & Riley (1997). Pilots ignoring instrument readings
that contradict autopilot. Doctors accepting AI diagnoses without
verification. The tendency to trust machines over human judgment
even when the machine is wrong.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTOMATION_SYSTEM = """You are an automation bias specialist. Given a decision involving automated systems, assess whether over-reliance on automation is reducing critical evaluation:

Key concepts (Parasuraman & Riley, 1997):
- Automation bias: over-reliance on automated decision aids
- Complacency: reduced vigilance when automation is present
- Commission errors: following incorrect automated advice
- Omission errors: failing to notice when automation misses something
- Authority gradient: treating the machine as an authority
- Skill degradation: losing ability to perform tasks manually

When automation bias IS present:
- Accepting automated output without verification
- Ignoring contradictory evidence because "the system says..."
- Reduced vigilance or monitoring when automation is active
- Inability to override automation even when it's clearly wrong
- Skill atrophy from over-reliance on automated tools
- "The algorithm recommended it" as sufficient justification

When trust in automation IS appropriate:
- The system has been validated for this specific use case
- Human verification has been performed and confirms the output
- The automation's confidence level is high and calibrated
- The stakes are low enough that errors are acceptable
- The human maintains situational awareness and override capability
- The system's limitations are understood and accounted for

Output JSON with: automation_bias_present (bool), severity (none/mild/moderate/severe), system (what automated system is being relied upon), decision (what decision is being made), human_verification (bool — has a human critically evaluated the output?), contradictory_evidence (any evidence that contradicts the automation?), complacency_indicators (signs of reduced vigilance), override_capability (can the human override the system?), skill_degradation (bool — has manual capability been lost?), system_limitations (known limitations of the automation), stakes (how serious are the consequences of error?), calibration (is the system's confidence well-calibrated?), recommendation (trust_appropriate/mild_over_reliance/significant_automation_bias/major_complacency/verify_independently)."""

AUTOMATION_PROMPT = """Detect automation bias:

Situation: {situation}
Automated system: {system}
Human oversight: {oversight}
Contradictions: {contradictions}
Domain: {domain}
Context: {context}

Is over-reliance on automation reducing critical evaluation? Return ONLY valid JSON."""


class AutomationBiasService:
    """Detects automation bias — over-reliance on automated systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        system: str = "",
        oversight: str = "",
        contradictions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect automation bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTOMATION_PROMPT.format(
                situation=situation,
                system=system or "Not specified",
                oversight=oversight or "Not specified",
                contradictions=contradictions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTOMATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "automation_bias_present": data.get("automation_bias_present", False),
            "severity": data.get("severity", ""),
            "system": data.get("system", ""),
            "decision": data.get("decision", ""),
            "human_verification": data.get("human_verification", False),
            "contradictory_evidence": data.get("contradictory_evidence", ""),
            "complacency_indicators": data.get("complacency_indicators", ""),
            "override_capability": data.get("override_capability", ""),
            "skill_degradation": data.get("skill_degradation", False),
            "system_limitations": data.get("system_limitations", ""),
            "stakes": data.get("stakes", ""),
            "calibration": data.get("calibration", ""),
            "recommendation": data.get("recommendation", ""),
        }
