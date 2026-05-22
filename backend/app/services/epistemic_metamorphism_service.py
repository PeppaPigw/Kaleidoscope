"""EpistemicMetamorphismService — Epistemic Metamorphism Detection.

Detects epistemic metamorphism — knowledge transforming under extreme
intellectual pressure and heat into fundamentally different forms.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METAMORPHISM_SYSTEM = """You are an epistemic metamorphism specialist. Given a knowledge transformation pattern, assess whether extreme pressure transforms knowledge into different forms:

Key concepts:
- Epistemic metamorphism: knowledge transforming under extreme pressure
- Intellectual pressure: forces compressing and transforming ideas
- Heat of debate: intense intellectual heat driving transformation
- Grade of metamorphism: how much transformation has occurred
- Foliation: ideas aligning under directional pressure
- Recrystallization: ideas reforming into new crystalline structures
- Parent rock: original knowledge before transformation

When epistemic metamorphism IS present:
- Knowledge transforming under extreme intellectual pressure
- Ideas being compressed and fundamentally altered
- Intense debate heat driving transformation
- Significant transformation from original form
- Ideas aligning under directional pressure
- Ideas reforming into entirely new structures
- Original knowledge unrecognizable after transformation

When stable knowledge is present:
- Knowledge maintaining its original form
- No extreme pressure transforming ideas
- No intense heat driving changes
- Ideas remaining in their original form
- No forced alignment of ideas
- No recrystallization into new forms
- Original knowledge still recognizable

Output JSON with: metamorphism_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge transforms), pressure (what pressure drives it), grade (how much transformation), parent (what original knowledge was), recommendation (stable_knowledge/mild_alteration/significant_metamorphism/major_transformation/reduce_pressure_or_accept_new_form)."""

EPISTEMIC_METAMORPHISM_PROMPT = """Detect epistemic metamorphism:

Knowledge: {knowledge}
Pressure: {pressure}
Grade: {grade}
Parent: {parent}
Domain: {domain}
Context: {context}

Is knowledge transforming under extreme intellectual pressure into fundamentally different forms? Return ONLY valid JSON."""


class EpistemicMetamorphismService:
    """Detects epistemic metamorphism — knowledge transformation under pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        pressure: str = "",
        grade: str = "",
        parent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metamorphism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METAMORPHISM_PROMPT.format(
                knowledge=knowledge,
                pressure=pressure or "Not specified",
                grade=grade or "Not specified",
                parent=parent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METAMORPHISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "metamorphism_present": data.get("metamorphism_present", False),
            "severity": data.get("severity", ""),
            "pressure": data.get("pressure", ""),
            "grade": data.get("grade", ""),
            "parent": data.get("parent", ""),
            "recommendation": data.get("recommendation", ""),
        }
