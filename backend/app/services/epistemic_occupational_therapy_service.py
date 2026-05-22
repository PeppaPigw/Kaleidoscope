"""EpistemicOccupationalTherapyService — Epistemic Occupational Therapy Detection.

Detects need for epistemic occupational therapy — relearning functional
intellectual activities of daily living after impairment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_OCCUPATIONAL_THERAPY_SYSTEM = """You are an epistemic occupational therapy specialist. Given intellectual functional limitations, assess whether activity relearning is needed:

Key concepts:
- Epistemic occupational therapy: relearning functional intellectual activities
- ADL: activities of daily intellectual living
- Adaptive equipment: tools to compensate for limitation
- Task analysis: breaking activities into manageable steps
- Environmental modification: changing context to enable function
- Energy conservation: managing limited intellectual resources
- Splinting: supporting weak intellectual structures

When epistemic occupational therapy IS needed:
- Inability to perform functional intellectual activities
- Daily intellectual activities impaired
- Need for compensatory tools
- Activities need breaking into steps
- Context needs modification for function
- Limited intellectual resources need managing
- Weak structures need external support

When no therapy needed:
- Full functional intellectual activity
- All daily activities performed
- No compensatory tools needed
- Activities performed fluidly
- Context supports function naturally
- Adequate intellectual resources
- Strong self-supporting structures

Output JSON with: occupational_therapy_needed (bool), severity (none/mild/moderate/severe), adl_impairment (what daily activity loss), adaptive_equipment (what compensatory tools), task_analysis (what step breakdown), energy_conservation (what resource management), recommendation (no_therapy_needed/mild_therapy/significant_rehabilitation/major_functional_retraining/comprehensive_intellectual_activity_program)."""

EPISTEMIC_OCCUPATIONAL_THERAPY_PROMPT = """Detect epistemic occupational therapy need:

ADL impairment: {adl_impairment}
Adaptive equipment: {adaptive_equipment}
Task analysis: {task_analysis}
Energy conservation: {energy_conservation}
Domain: {domain}
Context: {context}

Is relearning of functional intellectual activities needed? Return ONLY valid JSON."""


class EpistemicOccupationalTherapyService:
    """Detects epistemic occupational therapy need — functional activity relearning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        adl_impairment: str,
        *,
        adaptive_equipment: str = "",
        task_analysis: str = "",
        energy_conservation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic occupational therapy need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_OCCUPATIONAL_THERAPY_PROMPT.format(
                adl_impairment=adl_impairment,
                adaptive_equipment=adaptive_equipment or "Not specified",
                task_analysis=task_analysis or "Not specified",
                energy_conservation=energy_conservation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_OCCUPATIONAL_THERAPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "adl_impairment": adl_impairment[:200],
            "occupational_therapy_needed": data.get("occupational_therapy_needed", False),
            "severity": data.get("severity", ""),
            "adaptive_equipment": data.get("adaptive_equipment", ""),
            "task_analysis": data.get("task_analysis", ""),
            "energy_conservation": data.get("energy_conservation", ""),
            "recommendation": data.get("recommendation", ""),
        }
