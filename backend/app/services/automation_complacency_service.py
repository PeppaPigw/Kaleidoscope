"""AutomationComplacencyService — Automation Complacency Detection.

Detects automation complacency — over-trusting automated systems
and failing to maintain appropriate monitoring and skepticism.
Parasuraman & Manzey (2010). When systems work well most of
the time, humans stop checking. The automation paradox: the
better the system works, the less humans monitor it, and the
worse they perform when it fails.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTOMATION_COMPLACENCY_SYSTEM = """You are an automation complacency specialist. Given a human-automation interaction, assess whether appropriate monitoring and skepticism are being maintained:

Key concepts (Parasuraman & Manzey, 2010):
- Automation complacency: over-trusting automated systems
- Automation paradox: better automation = worse human monitoring
- Vigilance decrement: attention fades with reliable automation
- Out-of-the-loop: humans lose situational awareness
- Skill degradation: manual skills atrophy with automation
- Automation surprise: shock when automation fails unexpectedly
- Trust calibration: trust should match actual reliability

When automation complacency IS present:
- Blindly accepting automated outputs without verification
- "The system said so" as sufficient justification
- No manual checks or spot-verification of automated results
- Surprise when automation produces errors
- Loss of ability to perform the task manually
- Assuming automation is infallible
- No monitoring of automation performance over time

When trust in automation IS appropriate:
- The system has been validated for this specific use case
- Appropriate monitoring and verification are in place
- The human maintains ability to override and intervene
- Trust is calibrated to actual measured reliability
- Failure modes are understood and monitored for
- Regular manual checks maintain human competence

Output JSON with: automation_complacency_present (bool), severity (none/mild/moderate/severe), system (what automated system is involved), trust_level (how much is the system trusted), monitoring (what monitoring is in place), verification (what verification occurs), skill_maintenance (are manual skills maintained), failure_preparedness (how prepared for automation failure), recommendation (trust_calibrated/mild_over_trust/significant_complacency/major_blind_trust/implement_verification_and_monitoring)."""

AUTOMATION_COMPLACENCY_PROMPT = """Detect automation complacency:

Situation: {situation}
System: {system}
Monitoring: {monitoring}
Verification: {verification}
Domain: {domain}
Context: {context}

Is there over-trust in automated systems with insufficient monitoring and verification? Return ONLY valid JSON."""


class AutomationComplacencyService:
    """Detects automation complacency — over-trusting automated systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        system: str = "",
        monitoring: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect automation complacency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTOMATION_COMPLACENCY_PROMPT.format(
                situation=situation,
                system=system or "Not specified",
                monitoring=monitoring or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTOMATION_COMPLACENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "automation_complacency_present": data.get("automation_complacency_present", False),
            "severity": data.get("severity", ""),
            "trust_level": data.get("trust_level", ""),
            "monitoring": data.get("monitoring", ""),
            "verification": data.get("verification", ""),
            "skill_maintenance": data.get("skill_maintenance", ""),
            "failure_preparedness": data.get("failure_preparedness", ""),
            "recommendation": data.get("recommendation", ""),
        }
