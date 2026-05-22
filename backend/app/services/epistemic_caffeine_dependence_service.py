"""EpistemicCaffeineDependenceService — Epistemic Caffeine Dependence Detection.

Detects epistemic caffeine dependence — reliance on external intellectual
stimulants to maintain baseline cognitive function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAFFEINE_SYSTEM = """You are an epistemic caffeine dependence specialist. Given reliance on intellectual stimulants, assess dependence:

Key concepts:
- Epistemic caffeine dependence: reliance on external stimulants
- Tolerance: needing more stimulation for same effect
- Withdrawal: cognitive crash without stimulant
- Baseline shift: unable to function without stimulant
- Escalation: increasing stimulant intensity over time
- Functional dependence: performing only with stimulant
- Crash cycle: stimulant high followed by cognitive low

When epistemic caffeine dependence IS present:
- Reliance on external stimulants
- Needing more for same effect
- Crash without stimulant
- Cannot function without it
- Increasing intensity
- Only performing with stimulant
- High-low cycling

When no dependence:
- Self-sustained cognition
- Consistent performance
- No withdrawal effects
- Baseline function maintained
- Stable stimulation needs
- Independent performance
- Steady cognitive state

Output JSON with: dependence_detected (bool), severity (none/mild/moderate/severe), tolerance_level (what escalation), withdrawal_symptoms (what crash), baseline_function (what without stimulant), escalation_pattern (what increasing), recommendation (no_dependence/mild_gradual_reduction/significant_structured_taper/major_intensive_detox/emergency_complete_dependence)."""

EPISTEMIC_CAFFEINE_PROMPT = """Detect epistemic caffeine dependence:

Tolerance level: {tolerance_level}
Withdrawal symptoms: {withdrawal_symptoms}
Baseline function: {baseline_function}
Escalation pattern: {escalation_pattern}
Domain: {domain}
Context: {context}

Is there reliance on external intellectual stimulants to maintain baseline function? Return ONLY valid JSON."""


class EpistemicCaffeineDependenceService:
    """Detects epistemic caffeine dependence — stimulant reliance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tolerance_level: str,
        *,
        withdrawal_symptoms: str = "",
        baseline_function: str = "",
        escalation_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic caffeine dependence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAFFEINE_PROMPT.format(
                tolerance_level=tolerance_level,
                withdrawal_symptoms=withdrawal_symptoms or "Not specified",
                baseline_function=baseline_function or "Not specified",
                escalation_pattern=escalation_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAFFEINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tolerance_level": tolerance_level[:200],
            "dependence_detected": data.get("dependence_detected", False),
            "severity": data.get("severity", ""),
            "withdrawal_symptoms": data.get("withdrawal_symptoms", ""),
            "baseline_function": data.get("baseline_function", ""),
            "escalation_pattern": data.get("escalation_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
