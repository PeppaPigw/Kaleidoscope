"""EpistemicStimulantAbuseService — Epistemic Stimulant Abuse Detection.

Detects epistemic stimulant abuse — artificial intellectual enhancement
through unsustainable cognitive boosting methods.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STIMULANT_SYSTEM = """You are an epistemic stimulant abuse specialist. Given artificial intellectual enhancement, assess stimulant abuse:

Key concepts:
- Epistemic stimulant abuse: artificial cognitive enhancement
- Performance enhancement: boosting beyond natural capacity
- Crash cycle: enhancement followed by severe depletion
- Tolerance: needing more enhancement for same output
- Burnout: system damage from chronic overstimulation
- Unsustainability: enhancement cannot be maintained long-term
- Cognitive debt: borrowing future capacity for present output

When epistemic stimulant abuse IS present:
- Artificial cognitive enhancement
- Boosting beyond natural capacity
- Enhancement followed by depletion
- Needing more for same output
- System damage from overstimulation
- Cannot maintain long-term
- Borrowing future capacity

When no stimulant abuse:
- Natural cognitive capacity
- Sustainable performance
- No crash cycles
- Consistent output
- System health maintained
- Long-term sustainability
- No cognitive debt

Output JSON with: stimulant_abuse_detected (bool), severity (none/mild/moderate/severe), enhancement_method (what boosting), crash_pattern (what depletion), tolerance_level (what escalation), sustainability_assessment (what long-term viability), recommendation (no_stimulant_abuse/mild_sustainable_practices/significant_structured_reduction/major_intensive_recovery/emergency_severe_burnout)."""

EPISTEMIC_STIMULANT_PROMPT = """Detect epistemic stimulant abuse:

Enhancement method: {enhancement_method}
Crash pattern: {crash_pattern}
Tolerance level: {tolerance_level}
Sustainability assessment: {sustainability_assessment}
Domain: {domain}
Context: {context}

Is there artificial intellectual enhancement through unsustainable methods? Return ONLY valid JSON."""


class EpistemicStimulantAbuseService:
    """Detects epistemic stimulant abuse — artificial intellectual enhancement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        enhancement_method: str,
        *,
        crash_pattern: str = "",
        tolerance_level: str = "",
        sustainability_assessment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic stimulant abuse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STIMULANT_PROMPT.format(
                enhancement_method=enhancement_method,
                crash_pattern=crash_pattern or "Not specified",
                tolerance_level=tolerance_level or "Not specified",
                sustainability_assessment=sustainability_assessment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STIMULANT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "enhancement_method": enhancement_method[:200],
            "stimulant_abuse_detected": data.get("stimulant_abuse_detected", False),
            "severity": data.get("severity", ""),
            "crash_pattern": data.get("crash_pattern", ""),
            "tolerance_level": data.get("tolerance_level", ""),
            "sustainability_assessment": data.get("sustainability_assessment", ""),
            "recommendation": data.get("recommendation", ""),
        }
