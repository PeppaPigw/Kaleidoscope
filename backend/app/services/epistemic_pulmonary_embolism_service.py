"""EpistemicPulmonaryEmbolismService — Epistemic Pulmonary Embolism Detection.

Detects epistemic pulmonary embolism — blockage in intellectual circulation
cutting off idea supply to processing areas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PULMONARY_EMBOLISM_SYSTEM = """You are an epistemic pulmonary embolism specialist. Given intellectual circulation, assess whether blockage is cutting off idea supply:

Key concepts:
- Epistemic pulmonary embolism: blockage cutting off idea supply
- Thrombus: clot traveling to block circulation
- Infarction: tissue death from blocked supply
- Saddle embolus: massive blockage at main bifurcation
- Right heart strain: upstream system overloaded
- Ventilation without perfusion: ideas present but not circulating
- Anticoagulation: preventing further clot formation

When epistemic pulmonary embolism IS present:
- Blockage in intellectual circulation cutting off supply
- Clots traveling to block idea flow
- Intellectual tissue dying from blocked supply
- Massive blockage at main distribution points
- Upstream systems overloaded from blockage
- Ideas present but not reaching processing
- Need to prevent further blockage formation

When healthy circulation is present:
- No blockages in circulation
- No traveling clots
- No tissue death
- Clear distribution points
- Normal upstream load
- Ideas reaching all processing areas
- No anticoagulation needed

Output JSON with: pulmonary_embolism_present (bool), severity (none/mild/moderate/severe), thrombus (what traveling blockage), infarction (what tissue death), right_heart_strain (what upstream overload), dead_space (what ventilation without perfusion), recommendation (healthy_circulation/mild_embolism/significant_pulmonary_embolism/major_circulation_blockage/restore_intellectual_flow)."""

EPISTEMIC_PULMONARY_EMBOLISM_PROMPT = """Detect epistemic pulmonary embolism:

Thrombus: {thrombus}
Infarction: {infarction}
Right heart strain: {right_heart_strain}
Dead space: {dead_space}
Domain: {domain}
Context: {context}

Is blockage in intellectual circulation cutting off idea supply to processing areas? Return ONLY valid JSON."""


class EpistemicPulmonaryEmbolismService:
    """Detects epistemic pulmonary embolism — blockage cutting off idea supply."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thrombus: str,
        *,
        infarction: str = "",
        right_heart_strain: str = "",
        dead_space: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pulmonary embolism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PULMONARY_EMBOLISM_PROMPT.format(
                thrombus=thrombus,
                infarction=infarction or "Not specified",
                right_heart_strain=right_heart_strain or "Not specified",
                dead_space=dead_space or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PULMONARY_EMBOLISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thrombus": thrombus[:200],
            "pulmonary_embolism_present": data.get("pulmonary_embolism_present", False),
            "severity": data.get("severity", ""),
            "infarction": data.get("infarction", ""),
            "right_heart_strain": data.get("right_heart_strain", ""),
            "dead_space": data.get("dead_space", ""),
            "recommendation": data.get("recommendation", ""),
        }
