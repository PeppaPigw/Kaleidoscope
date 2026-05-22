"""EpistemicTestimonyDetailIllusionService — Epistemic Testimony Detail Illusion Detection.

Detects epistemic testimony detail illusion — treating vivid, specific detail in
testimony as evidence of truthfulness when detail and accuracy are independent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TESTIMONY_DETAIL_ILLUSION_SYSTEM = """You are an epistemic testimony detail illusion specialist. Given detail-as-truth reasoning, assess distortion:

Key concepts:
- Epistemic detail illusion: vivid detail treated as truth indicator
- Specificity heuristic: specific claims assumed more accurate than vague
- Narrative richness: rich storytelling assumed more truthful
- Sensory detail: sensory descriptions creating credibility
- Peripheral detail: irrelevant details creating overall credibility
- Confabulation blindness: ignoring that false memories are often detailed
- Fabrication sophistication: sophisticated lies being more detailed than truth

When epistemic detail illusion IS present:
- Vivid detail treated as truth
- Specificity assumed as accuracy
- Rich narrative assumed truthful
- Sensory details creating credibility
- Peripheral details boosting belief
- Confabulation possibility ignored
- Fabrication sophistication missed

When no detail illusion:
- Detail separated from truth
- Specificity not assumed as accuracy
- Narrative richness not conflated with truth
- Sensory details not privileged
- Peripheral details not boosting credibility
- Confabulation considered
- Fabrication possibility assessed

Output JSON with: detail_illusion_detected (bool), severity (none/mild/moderate/severe), specificity_heuristic (what specificity assumed as accuracy), narrative_richness (what richness assumed truthful), confabulation_blindness (what confabulation ignored), fabrication_sophistication (what fabrication missed), recommendation (no_detail_illusion/mild_detail_skepticism/significant_verification_requirement/major_intensive_corroboration_demand/emergency_complete_detail_illusion)."""

EPISTEMIC_TESTIMONY_DETAIL_ILLUSION_PROMPT = """Detect epistemic testimony detail illusion:

Specificity heuristic: {specificity_heuristic}
Narrative richness: {narrative_richness}
Confabulation blindness: {confabulation_blindness}
Fabrication sophistication: {fabrication_sophistication}
Domain: {domain}
Context: {context}

Is vivid detail being treated as evidence of truthfulness? Return ONLY valid JSON."""


class EpistemicTestimonyDetailIllusionService:
    """Detects epistemic testimony detail illusion — detail as truth indicator."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        specificity_heuristic: str,
        *,
        narrative_richness: str = "",
        confabulation_blindness: str = "",
        fabrication_sophistication: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic testimony detail illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TESTIMONY_DETAIL_ILLUSION_PROMPT.format(
                specificity_heuristic=specificity_heuristic,
                narrative_richness=narrative_richness or "Not specified",
                confabulation_blindness=confabulation_blindness or "Not specified",
                fabrication_sophistication=fabrication_sophistication or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TESTIMONY_DETAIL_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "specificity_heuristic": specificity_heuristic[:200],
            "detail_illusion_detected": data.get("detail_illusion_detected", False),
            "severity": data.get("severity", ""),
            "narrative_richness": data.get("narrative_richness", ""),
            "confabulation_blindness": data.get("confabulation_blindness", ""),
            "fabrication_sophistication": data.get("fabrication_sophistication", ""),
            "recommendation": data.get("recommendation", ""),
        }
