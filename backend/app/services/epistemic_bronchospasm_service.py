"""EpistemicBronchospasmService — Epistemic Bronchospasm Detection.

Detects epistemic bronchospasm — sudden constriction of intellectual
airways limiting the flow of ideas through the system.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRONCHOSPASM_SYSTEM = """You are an epistemic bronchospasm specialist. Given intellectual airways, assess whether sudden constriction is limiting idea flow:

Key concepts:
- Epistemic bronchospasm: sudden constriction of intellectual airways
- Smooth muscle contraction: airways narrowing reflexively
- Trigger: stimulus causing the constriction
- Bronchodilation: opening the constricted airways
- Hyperreactivity: airways overly sensitive to triggers
- Mucus plugging: additional obstruction from secretions
- Air trapping: ideas unable to exit due to constriction

When epistemic bronchospasm IS present:
- Sudden constriction of intellectual airways
- Reflexive narrowing of idea flow channels
- Specific triggers causing constriction
- Need for interventions to open airways
- Overly sensitive intellectual channels
- Additional obstruction from accumulated material
- Ideas trapped unable to exit

When healthy airways are present:
- Open intellectual airways
- No reflexive narrowing
- No trigger sensitivity
- No bronchodilation needed
- Normal airway reactivity
- No mucus plugging
- Free idea flow in and out

Output JSON with: bronchospasm_present (bool), severity (none/mild/moderate/severe), smooth_muscle_contraction (what reflexive narrowing), trigger (what stimulus), hyperreactivity (what oversensitivity), air_trapping (what exit blockage), recommendation (healthy_airways/mild_bronchospasm/significant_bronchospasm/major_airway_constriction/open_intellectual_airways)."""

EPISTEMIC_BRONCHOSPASM_PROMPT = """Detect epistemic bronchospasm:

Smooth muscle contraction: {smooth_muscle_contraction}
Trigger: {trigger}
Hyperreactivity: {hyperreactivity}
Air trapping: {air_trapping}
Domain: {domain}
Context: {context}

Is sudden constriction of intellectual airways limiting idea flow? Return ONLY valid JSON."""


class EpistemicBronchospasmService:
    """Detects epistemic bronchospasm — sudden constriction limiting idea flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        smooth_muscle_contraction: str,
        *,
        trigger: str = "",
        hyperreactivity: str = "",
        air_trapping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bronchospasm."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRONCHOSPASM_PROMPT.format(
                smooth_muscle_contraction=smooth_muscle_contraction,
                trigger=trigger or "Not specified",
                hyperreactivity=hyperreactivity or "Not specified",
                air_trapping=air_trapping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRONCHOSPASM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "smooth_muscle_contraction": smooth_muscle_contraction[:200],
            "bronchospasm_present": data.get("bronchospasm_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "hyperreactivity": data.get("hyperreactivity", ""),
            "air_trapping": data.get("air_trapping", ""),
            "recommendation": data.get("recommendation", ""),
        }
