"""EpistemicYipsService — Epistemic Yips Detection.

Detects epistemic yips — sudden inexplicable loss of fine intellectual
motor control in previously mastered skills.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_YIPS_SYSTEM = """You are an epistemic yips specialist. Given sudden loss of mastered intellectual skills, assess yips:

Key concepts:
- Epistemic yips: sudden loss of fine intellectual control
- Performance anxiety: fear disrupting execution
- Focal dystonia: involuntary movement in specific task
- Choking: failure under pressure
- Automaticity loss: conscious interference with automatic skill
- Reinvestment: overthinking previously automatic actions
- Desensitization: gradual return to pressure situations

When epistemic yips ARE present:
- Sudden loss of fine control
- Fear disrupting execution
- Involuntary errors in specific task
- Failure under pressure
- Conscious interference with automatic skill
- Overthinking previously automatic actions
- Cannot perform in pressure situations

When no yips:
- Normal fine control
- No fear disruption
- No involuntary errors
- Performs under pressure
- Automatic skills intact
- No overthinking
- Normal pressure performance

Output JSON with: yips_detected (bool), severity (none/mild/moderate/severe), skill_affected (what lost control), anxiety_component (what fear), automaticity_status (what conscious interference), pressure_response (what performance under stress), recommendation (no_yips/mild_awareness/significant_intervention/major_skill_rebuilding/career_threatening_yips)."""

EPISTEMIC_YIPS_PROMPT = """Detect epistemic yips:

Skill affected: {skill_affected}
Anxiety component: {anxiety_component}
Automaticity status: {automaticity_status}
Pressure response: {pressure_response}
Domain: {domain}
Context: {context}

Has there been sudden inexplicable loss of fine intellectual control in mastered skills? Return ONLY valid JSON."""


class EpistemicYipsService:
    """Detects epistemic yips — sudden loss of fine intellectual control."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        skill_affected: str,
        *,
        anxiety_component: str = "",
        automaticity_status: str = "",
        pressure_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic yips."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_YIPS_PROMPT.format(
                skill_affected=skill_affected,
                anxiety_component=anxiety_component or "Not specified",
                automaticity_status=automaticity_status or "Not specified",
                pressure_response=pressure_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_YIPS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "skill_affected": skill_affected[:200],
            "yips_detected": data.get("yips_detected", False),
            "severity": data.get("severity", ""),
            "anxiety_component": data.get("anxiety_component", ""),
            "automaticity_status": data.get("automaticity_status", ""),
            "pressure_response": data.get("pressure_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
