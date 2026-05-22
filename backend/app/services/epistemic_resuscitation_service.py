"""EpistemicResuscitationService — Epistemic Resuscitation Detection.

Detects need for epistemic resuscitation — reviving intellectual systems
that have stopped functioning, restoring vital intellectual signs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RESUSCITATION_SYSTEM = """You are an epistemic resuscitation specialist. Given intellectual systems that have stopped, assess whether revival is possible:

Key concepts:
- Epistemic resuscitation: reviving stopped intellectual systems
- CPR: chest compressions and breathing for intellectual circulation
- Defibrillation: electrical shock to restart intellectual rhythm
- ROSC: return of spontaneous intellectual circulation
- Brain death: irreversible loss of intellectual function
- Hypothermia protocol: cooling to preserve function during arrest
- Chain of survival: sequence of actions for best outcome

When epistemic resuscitation IS needed:
- Intellectual systems have stopped functioning
- Need for compressions to maintain circulation
- Need for shock to restart rhythm
- Possibility of spontaneous return
- Risk of irreversible function loss
- Need for preservation during arrest
- Critical sequence of actions required

When no resuscitation needed:
- Systems functioning normally
- Normal intellectual circulation
- Normal intellectual rhythm
- Spontaneous function maintained
- No risk of irreversible loss
- No preservation needed
- Normal ongoing function

Output JSON with: resuscitation_needed (bool), severity (none/mild/moderate/severe), arrest_type (what stopped), rosc_potential (what return possibility), brain_death_risk (what irreversibility), chain_of_survival (what sequence needed), recommendation (no_resuscitation_needed/mild_support/significant_resuscitation/major_full_code/initiate_intellectual_cpr)."""

EPISTEMIC_RESUSCITATION_PROMPT = """Detect epistemic resuscitation need:

Arrest type: {arrest_type}
ROSC potential: {rosc_potential}
Brain death risk: {brain_death_risk}
Chain of survival: {chain_of_survival}
Domain: {domain}
Context: {context}

Have intellectual systems stopped functioning and can they be revived? Return ONLY valid JSON."""


class EpistemicResuscitationService:
    """Detects epistemic resuscitation need — reviving stopped intellectual systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        arrest_type: str,
        *,
        rosc_potential: str = "",
        brain_death_risk: str = "",
        chain_of_survival: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic resuscitation need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RESUSCITATION_PROMPT.format(
                arrest_type=arrest_type,
                rosc_potential=rosc_potential or "Not specified",
                brain_death_risk=brain_death_risk or "Not specified",
                chain_of_survival=chain_of_survival or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RESUSCITATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "arrest_type": arrest_type[:200],
            "resuscitation_needed": data.get("resuscitation_needed", False),
            "severity": data.get("severity", ""),
            "rosc_potential": data.get("rosc_potential", ""),
            "brain_death_risk": data.get("brain_death_risk", ""),
            "chain_of_survival": data.get("chain_of_survival", ""),
            "recommendation": data.get("recommendation", ""),
        }
