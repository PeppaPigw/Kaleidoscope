"""HermeneuticalInjusticeService — Hermeneutical Injustice Detection.

Detects hermeneutical injustice — lacking conceptual resources to
understand or articulate one's own experience due to structural
gaps in collective interpretive resources.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HERMENEUTICAL_INJUSTICE_SYSTEM = """You are a hermeneutical injustice specialist. Given a situation, assess whether there are structural gaps in interpretive resources that prevent understanding:

Key concepts:
- Hermeneutical injustice: gaps in collective interpretive resources
- Conceptual lacuna: missing concepts for experiences
- Interpretive marginalization: some experiences lack vocabulary
- Structural epistemic gap: systematic absence of understanding
- Pre-conceptual experience: experience without adequate concepts
- Hermeneutical marginalization: excluded from meaning-making
- Collective interpretive resources: shared concepts and frameworks

When hermeneutical injustice IS present:
- Experience lacks adequate conceptual resources
- Structural gaps prevent articulation of experience
- Dominant frameworks don't capture certain experiences
- Marginalized experiences lack vocabulary
- Interpretive resources systematically exclude some
- Experience dismissed because no concept exists for it
- Meaning-making resources controlled by dominant group

When interpretive difficulty is appropriate:
- Genuine novelty of experience (not structural exclusion)
- Concepts being developed through normal inquiry
- Difficulty reflects genuine complexity, not exclusion
- Multiple frameworks available for interpretation
- Interpretive resources accessible to all
- Gaps being actively addressed
- Difficulty not systematically patterned

Output JSON with: injustice_present (bool), severity (none/mild/moderate/severe), experience (what experience lacks resources), gap (what conceptual gap exists), structural_cause (what structural factor causes the gap), impact (how the gap affects understanding), recommendation (appropriate_interpretive_challenge/mild_conceptual_gap/significant_hermeneutical_injustice/major_interpretive_exclusion/develop_adequate_concepts)."""

HERMENEUTICAL_INJUSTICE_PROMPT = """Detect hermeneutical injustice:

Situation: {situation}
Experience: {experience}
Available concepts: {concepts}
Structural factors: {structural}
Domain: {domain}
Context: {context}

Are there structural gaps in interpretive resources preventing understanding of certain experiences? Return ONLY valid JSON."""


class HermeneuticalInjusticeService:
    """Detects hermeneutical injustice — structural gaps in interpretive resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        experience: str = "",
        concepts: str = "",
        structural: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hermeneutical injustice."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HERMENEUTICAL_INJUSTICE_PROMPT.format(
                situation=situation,
                experience=experience or "Not specified",
                concepts=concepts or "Not specified",
                structural=structural or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HERMENEUTICAL_INJUSTICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "injustice_present": data.get("injustice_present", False),
            "severity": data.get("severity", ""),
            "gap": data.get("gap", ""),
            "structural_cause": data.get("structural_cause", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
