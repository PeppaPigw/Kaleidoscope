"""EpistemicLaborInductionService — Epistemic Labor Induction Detection.

Detects need for epistemic labor induction — artificially starting the
birth process of an intellectual creation that won't emerge naturally.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LABOR_INDUCTION_SYSTEM = """You are an epistemic labor induction specialist. Given intellectual creations that won't emerge naturally, assess induction need:

Key concepts:
- Epistemic labor induction: artificially starting intellectual birth
- Post-dates: creation overdue beyond expected delivery
- Oxytocin: agent to stimulate intellectual contractions
- Cervical ripening: preparing the pathway for delivery
- Bishop score: readiness assessment for induction
- Failed induction: stimulation not producing progress
- Augmentation: strengthening existing weak labor

When epistemic labor induction IS needed:
- Intellectual creation overdue
- Natural emergence not occurring
- Stimulation of contractions needed
- Pathway preparation required
- Low readiness score
- Previous stimulation failed
- Weak existing labor needing strengthening

When no induction needed:
- Creation emerging naturally
- On schedule for delivery
- Natural contractions adequate
- Pathway ready
- High readiness score
- Normal progress
- Strong natural labor

Output JSON with: induction_needed (bool), severity (none/mild/moderate/severe), overdue_status (what delay), readiness_score (what preparation level), stimulation_plan (what approach), failure_risk (what non-progress risk), recommendation (no_induction_needed/mild_augmentation/significant_induction/major_aggressive_induction/emergency_immediate_delivery)."""

EPISTEMIC_LABOR_INDUCTION_PROMPT = """Detect epistemic labor induction need:

Overdue status: {overdue_status}
Readiness score: {readiness_score}
Stimulation plan: {stimulation_plan}
Failure risk: {failure_risk}
Domain: {domain}
Context: {context}

Is an intellectual creation overdue and not emerging naturally? Return ONLY valid JSON."""


class EpistemicLaborInductionService:
    """Detects epistemic labor induction need — starting intellectual birth artificially."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        overdue_status: str,
        *,
        readiness_score: str = "",
        stimulation_plan: str = "",
        failure_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic labor induction need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LABOR_INDUCTION_PROMPT.format(
                overdue_status=overdue_status,
                readiness_score=readiness_score or "Not specified",
                stimulation_plan=stimulation_plan or "Not specified",
                failure_risk=failure_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LABOR_INDUCTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "overdue_status": overdue_status[:200],
            "induction_needed": data.get("induction_needed", False),
            "severity": data.get("severity", ""),
            "readiness_score": data.get("readiness_score", ""),
            "stimulation_plan": data.get("stimulation_plan", ""),
            "failure_risk": data.get("failure_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
