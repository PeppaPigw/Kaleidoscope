"""EpistemicCardiacArrestService — Epistemic Cardiac Arrest Detection.

Detects epistemic cardiac arrest — sudden cessation of intellectual
circulation, where idea flow stops completely and abruptly.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CARDIAC_ARREST_SYSTEM = """You are an epistemic cardiac arrest specialist. Given an intellectual circulation system, assess whether idea flow has suddenly ceased:

Key concepts:
- Epistemic cardiac arrest: sudden cessation of intellectual circulation
- Asystole: complete absence of intellectual activity
- Ventricular fibrillation: chaotic uncoordinated activity replacing flow
- Pulseless electrical activity: appearance of function without actual flow
- Chain of survival: steps needed to restore circulation
- Defibrillation: shock to restore normal rhythm
- CPR: manual forcing of circulation when pump fails

When epistemic cardiac arrest IS present:
- Sudden complete cessation of idea flow
- Complete absence of intellectual activity
- Chaotic uncoordinated activity replacing normal flow
- Appearance of function without actual circulation
- Need for emergency restoration steps
- Shock interventions to restart normal rhythm
- Manual forcing of intellectual circulation

When healthy circulation is present:
- Continuous idea flow
- Regular intellectual activity
- Coordinated productive output
- Genuine functional circulation
- No emergency needed
- Normal rhythm maintained
- Self-sustaining circulation

Output JSON with: cardiac_arrest_present (bool), severity (none/mild/moderate/severe), asystole (what complete absence), fibrillation (what chaotic activity), pulseless_activity (what false function), chain_of_survival (what restoration steps), recommendation (healthy_circulation/mild_arrest/significant_cardiac_arrest/major_circulation_failure/emergency_resuscitation)."""

EPISTEMIC_CARDIAC_ARREST_PROMPT = """Detect epistemic cardiac arrest:

Asystole: {asystole}
Fibrillation: {fibrillation}
Pulseless activity: {pulseless_activity}
Chain of survival: {chain_of_survival}
Domain: {domain}
Context: {context}

Has intellectual circulation suddenly ceased, with idea flow stopping completely? Return ONLY valid JSON."""


class EpistemicCardiacArrestService:
    """Detects epistemic cardiac arrest — sudden cessation of intellectual circulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        asystole: str,
        *,
        fibrillation: str = "",
        pulseless_activity: str = "",
        chain_of_survival: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cardiac arrest."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CARDIAC_ARREST_PROMPT.format(
                asystole=asystole,
                fibrillation=fibrillation or "Not specified",
                pulseless_activity=pulseless_activity or "Not specified",
                chain_of_survival=chain_of_survival or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CARDIAC_ARREST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "asystole": asystole[:200],
            "cardiac_arrest_present": data.get("cardiac_arrest_present", False),
            "severity": data.get("severity", ""),
            "fibrillation": data.get("fibrillation", ""),
            "pulseless_activity": data.get("pulseless_activity", ""),
            "chain_of_survival": data.get("chain_of_survival", ""),
            "recommendation": data.get("recommendation", ""),
        }
