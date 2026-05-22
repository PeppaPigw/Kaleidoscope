"""EpistemicProductivityAddictionService — Epistemic Productivity Addiction Detection.

Detects epistemic productivity addiction — compulsive need for intellectual
output, unable to rest or be without producing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRODUCTIVITY_ADDICTION_SYSTEM = """You are an epistemic productivity addiction specialist. Given compulsive need for output, assess addiction:

Key concepts:
- Epistemic productivity addiction: compulsive need to produce
- Rest inability: can't stop intellectual production
- Worth through output: value only from what produced
- Quantity over quality: volume matters more than depth
- Guilt when idle: shame when not producing
- Burnout cycle: produce until collapse then restart
- Being vs doing: can't just be intellectually present

When epistemic productivity addiction IS present:
- Compulsive need to produce
- Can't stop production
- Value only from output
- Volume over depth
- Shame when not producing
- Produce until collapse
- Can't just be present

When no productivity addiction:
- Balanced production
- Able to rest
- Value beyond output
- Quality valued
- Comfortable when idle
- Sustainable pace
- Being and doing balanced

Output JSON with: productivity_addiction_detected (bool), severity (none/mild/moderate/severe), rest_inability (what can't stop), worth_through_output (what valuing only), guilt_when_idle (what shame), burnout_cycle (what collapsing), recommendation (no_productivity_addiction/mild_rest_practice/significant_pace_reduction/major_intensive_addiction_work/emergency_severe_burnout)."""

EPISTEMIC_PRODUCTIVITY_ADDICTION_PROMPT = """Detect epistemic productivity addiction:

Rest inability: {rest_inability}
Worth through output: {worth_through_output}
Guilt when idle: {guilt_when_idle}
Burnout cycle: {burnout_cycle}
Domain: {domain}
Context: {context}

Is there compulsive need for intellectual output unable to rest? Return ONLY valid JSON."""


class EpistemicProductivityAddictionService:
    """Detects epistemic productivity addiction — compulsive need to produce."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rest_inability: str,
        *,
        worth_through_output: str = "",
        guilt_when_idle: str = "",
        burnout_cycle: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic productivity addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRODUCTIVITY_ADDICTION_PROMPT.format(
                rest_inability=rest_inability,
                worth_through_output=worth_through_output or "Not specified",
                guilt_when_idle=guilt_when_idle or "Not specified",
                burnout_cycle=burnout_cycle or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRODUCTIVITY_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rest_inability": rest_inability[:200],
            "productivity_addiction_detected": data.get("productivity_addiction_detected", False),
            "severity": data.get("severity", ""),
            "worth_through_output": data.get("worth_through_output", ""),
            "guilt_when_idle": data.get("guilt_when_idle", ""),
            "burnout_cycle": data.get("burnout_cycle", ""),
            "recommendation": data.get("recommendation", ""),
        }
