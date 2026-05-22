"""EpistemicGeneralAnesthesiaService — Epistemic General Anesthesia Detection.

Detects epistemic general anesthesia — complete suppression of intellectual
consciousness for major procedures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GENERAL_ANESTHESIA_SYSTEM = """You are an epistemic general anesthesia specialist. Given need for complete intellectual suppression, assess general anesthesia:

Key concepts:
- Epistemic general anesthesia: complete consciousness suppression
- Induction: process of achieving unconsciousness
- Maintenance: keeping unconscious during procedure
- Emergence: returning to consciousness
- Depth monitoring: ensuring adequate suppression
- Malignant hyperthermia: dangerous reaction to agents
- Awareness: unintended consciousness during procedure

When epistemic general anesthesia IS needed:
- Major intellectual procedure requiring unconsciousness
- Induction of complete suppression needed
- Maintenance of unconsciousness required
- Controlled emergence planned
- Depth monitoring available
- Reaction risks assessed
- Awareness prevention ensured

When no general anesthesia needed:
- Minor procedure manageable awake
- No complete suppression needed
- Local anesthesia sufficient
- No unconsciousness required
- No depth monitoring needed
- No reaction risk
- Awareness acceptable

Output JSON with: general_anesthesia_needed (bool), severity (none/mild/moderate/severe), induction_plan (what suppression approach), maintenance_strategy (what sustaining method), emergence_plan (what awakening approach), complication_risk (what danger), recommendation (no_general_needed/mild_conscious_sedation/significant_deep_sedation/major_general_anesthesia/emergency_rapid_sequence)."""

EPISTEMIC_GENERAL_ANESTHESIA_PROMPT = """Detect epistemic general anesthesia need:

Induction plan: {induction_plan}
Maintenance strategy: {maintenance_strategy}
Emergence plan: {emergence_plan}
Complication risk: {complication_risk}
Domain: {domain}
Context: {context}

Does the intellectual procedure require complete consciousness suppression? Return ONLY valid JSON."""


class EpistemicGeneralAnesthesiaService:
    """Detects epistemic general anesthesia need — complete consciousness suppression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        induction_plan: str,
        *,
        maintenance_strategy: str = "",
        emergence_plan: str = "",
        complication_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic general anesthesia need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GENERAL_ANESTHESIA_PROMPT.format(
                induction_plan=induction_plan,
                maintenance_strategy=maintenance_strategy or "Not specified",
                emergence_plan=emergence_plan or "Not specified",
                complication_risk=complication_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GENERAL_ANESTHESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "induction_plan": induction_plan[:200],
            "general_anesthesia_needed": data.get("general_anesthesia_needed", False),
            "severity": data.get("severity", ""),
            "maintenance_strategy": data.get("maintenance_strategy", ""),
            "emergence_plan": data.get("emergence_plan", ""),
            "complication_risk": data.get("complication_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
