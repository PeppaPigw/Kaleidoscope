"""EpistemicInactionGuiltService — Epistemic Inaction Guilt Detection.

Detects epistemic inaction guilt — guilt over not using knowledge
to help others or make a difference.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INACTION_GUILT_SYSTEM = """You are an epistemic inaction guilt specialist. Given guilt over not using knowledge to help, assess inaction guilt:

Key concepts:
- Epistemic inaction guilt: guilt over not using knowledge to help
- Unused potential: guilt about knowledge not applied
- Bystander guilt: knowing and not acting
- Teaching failure: guilt about not sharing knowledge
- Impact deficit: guilt about not making a difference
- Hoarding shame: guilt about keeping knowledge to oneself
- Obligation unfulfilled: feeling duty to use knowledge

When epistemic inaction guilt IS present:
- Guilt over not using knowledge
- Guilt about unused potential
- Knowing and not acting
- Guilt about not sharing
- Guilt about no impact
- Guilt about keeping to self
- Feeling unfulfilled duty

When no inaction guilt:
- Comfortable with pace
- Accepting limitations
- Acting when possible
- Sharing appropriately
- Realistic about impact
- Balanced sharing
- Healthy boundaries

Output JSON with: inaction_guilt_detected (bool), severity (none/mild/moderate/severe), unused_potential (what not applying), bystander_guilt (what not acting on), teaching_failure (what not sharing), impact_deficit (what not making difference about), recommendation (no_inaction_guilt/mild_action_planning/significant_boundary_work/major_intensive_guilt_processing/emergency_paralyzing_obligation)."""

EPISTEMIC_INACTION_GUILT_PROMPT = """Detect epistemic inaction guilt:

Unused potential: {unused_potential}
Bystander guilt: {bystander_guilt}
Teaching failure: {teaching_failure}
Impact deficit: {impact_deficit}
Domain: {domain}
Context: {context}

Is there guilt over not using knowledge to help others? Return ONLY valid JSON."""


class EpistemicInactionGuiltService:
    """Detects epistemic inaction guilt — guilt over not using knowledge to help."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        unused_potential: str,
        *,
        bystander_guilt: str = "",
        teaching_failure: str = "",
        impact_deficit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inaction guilt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INACTION_GUILT_PROMPT.format(
                unused_potential=unused_potential,
                bystander_guilt=bystander_guilt or "Not specified",
                teaching_failure=teaching_failure or "Not specified",
                impact_deficit=impact_deficit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INACTION_GUILT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "unused_potential": unused_potential[:200],
            "inaction_guilt_detected": data.get("inaction_guilt_detected", False),
            "severity": data.get("severity", ""),
            "bystander_guilt": data.get("bystander_guilt", ""),
            "teaching_failure": data.get("teaching_failure", ""),
            "impact_deficit": data.get("impact_deficit", ""),
            "recommendation": data.get("recommendation", ""),
        }
