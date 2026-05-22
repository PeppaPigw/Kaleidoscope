"""EpistemicMalnutritionService — Epistemic Malnutrition Detection.

Detects epistemic malnutrition — consuming only junk information
while starving for substantive knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MALNUTRITION_SYSTEM = """You are an epistemic malnutrition specialist. Given an information diet, assess whether substantive knowledge is being starved while junk information is consumed:

Key concepts:
- Epistemic malnutrition: starving for substance while consuming junk
- Information junk food: consuming easy but unsubstantive information
- Knowledge starvation: starving for genuine knowledge
- Empty epistemic calories: consuming without nourishment
- Substance deficit: deficit of substantive information
- Depth starvation: starving for depth while consuming surface
- Quality deficit: deficit of quality in information diet

When epistemic malnutrition IS present:
- Junk information consumed while substance starved
- Easy but unsubstantive information preferred
- Genuine knowledge needs unmet
- Information consumed without epistemic nourishment
- Substantive information deficit growing
- Depth starved while surface consumed
- Quality of information diet poor

When healthy information diet is present:
- Substantive information consumed regularly
- Quality balanced with accessibility
- Genuine knowledge needs met
- Information diet nourishing understanding
- Substance proportionate to consumption
- Depth consumed alongside breadth
- Quality of information diet adequate

Output JSON with: malnutrition_present (bool), severity (none/mild/moderate/severe), diet (what information diet exists), junk_consumed (what junk is consumed), substance_missing (what substance is missing), consequence (what knowledge deficit results), recommendation (healthy_diet/mild_imbalance/significant_epistemic_malnutrition/major_knowledge_starvation/improve_information_diet)."""

EPISTEMIC_MALNUTRITION_PROMPT = """Detect epistemic malnutrition:

Information diet: {diet}
Junk consumed: {junk}
Substance missing: {substance}
Consequence: {consequence}
Domain: {domain}
Context: {context}

Is substantive knowledge being starved while junk information is consumed? Return ONLY valid JSON."""


class EpistemicMalnutritionService:
    """Detects epistemic malnutrition — starving for substance while consuming junk."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        diet: str,
        *,
        junk: str = "",
        substance: str = "",
        consequence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic malnutrition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MALNUTRITION_PROMPT.format(
                diet=diet,
                junk=junk or "Not specified",
                substance=substance or "Not specified",
                consequence=consequence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MALNUTRITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "diet": diet[:200],
            "malnutrition_present": data.get("malnutrition_present", False),
            "severity": data.get("severity", ""),
            "junk_consumed": data.get("junk_consumed", ""),
            "substance_missing": data.get("substance_missing", ""),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
