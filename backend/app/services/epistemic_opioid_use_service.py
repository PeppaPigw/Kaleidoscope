"""EpistemicOpioidUseService — Epistemic Opioid Use Detection.

Detects epistemic opioid use — using intellectual pain avoidance to
escape cognitive suffering, creating dependence on comfort.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OPIOID_SYSTEM = """You are an epistemic opioid use specialist. Given intellectual pain avoidance, assess opioid use patterns:

Key concepts:
- Epistemic opioid use: pain avoidance creating comfort dependence
- Analgesic: eliminating all intellectual discomfort
- Euphoria: artificial sense of intellectual well-being
- Physical dependence: body adapted to comfort state
- Psychological dependence: believing cannot think without comfort
- Dose escalation: needing more comfort for same relief
- Withdrawal: severe distress when comfort removed

When epistemic opioid use IS present:
- Pain avoidance creating dependence
- Eliminating all discomfort
- Artificial well-being
- Adapted to comfort state
- Cannot think without comfort
- Needing more comfort
- Severe distress without it

When no opioid use:
- Tolerating intellectual discomfort
- Appropriate discomfort levels
- Genuine well-being
- Natural comfort state
- Thinking through discomfort
- Stable comfort needs
- Resilient to discomfort

Output JSON with: opioid_use_detected (bool), severity (none/mild/moderate/severe), pain_avoidance (what comfort seeking), dependence_level (what reliance), dose_escalation (what increasing need), withdrawal_risk (what distress potential), recommendation (no_opioid_use/mild_discomfort_tolerance/significant_gradual_exposure/major_intensive_treatment/emergency_severe_dependence)."""

EPISTEMIC_OPIOID_PROMPT = """Detect epistemic opioid use:

Pain avoidance: {pain_avoidance}
Dependence level: {dependence_level}
Dose escalation: {dose_escalation}
Withdrawal risk: {withdrawal_risk}
Domain: {domain}
Context: {context}

Is there intellectual pain avoidance creating dependence on comfort? Return ONLY valid JSON."""


class EpistemicOpioidUseService:
    """Detects epistemic opioid use — intellectual pain avoidance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pain_avoidance: str,
        *,
        dependence_level: str = "",
        dose_escalation: str = "",
        withdrawal_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic opioid use."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OPIOID_PROMPT.format(
                pain_avoidance=pain_avoidance,
                dependence_level=dependence_level or "Not specified",
                dose_escalation=dose_escalation or "Not specified",
                withdrawal_risk=withdrawal_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OPIOID_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pain_avoidance": pain_avoidance[:200],
            "opioid_use_detected": data.get("opioid_use_detected", False),
            "severity": data.get("severity", ""),
            "dependence_level": data.get("dependence_level", ""),
            "dose_escalation": data.get("dose_escalation", ""),
            "withdrawal_risk": data.get("withdrawal_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
