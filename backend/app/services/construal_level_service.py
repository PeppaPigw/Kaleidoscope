"""ConstrualLevelService — Construal Level Bias Detection.

Detects construal level bias — psychological distance (temporal,
spatial, social, hypothetical) causing inappropriate abstraction
or concreteness in judgment. Trope & Liberman (2010). Distant
things are construed abstractly (why), near things concretely (how).
This distorts planning, empathy, and risk assessment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONSTRUAL_LEVEL_SYSTEM = """You are a construal level theory specialist. Given a judgment or decision, assess whether psychological distance is causing inappropriate abstraction or concreteness:

Key concepts (Trope & Liberman, 2010):
- Construal level: abstract (high) vs concrete (low) mental representation
- Psychological distance: temporal, spatial, social, hypothetical
- High construal: why, desirability, goals, principles, categories
- Low construal: how, feasibility, means, details, exemplars
- Distance-abstraction link: far = abstract, near = concrete
- Planning fallacy interaction: distant plans stay abstract, miss details
- Empathy gap interaction: distant others construed abstractly

When construal level IS distorting:
- Planning distant events without concrete feasibility analysis
- Judging distant others by abstract principles, near others by context
- Overweighting desirability for distant choices, feasibility for near ones
- "In principle" reasoning for situations requiring practical detail
- Concrete thinking about abstract problems (missing the forest for trees)
- Abstract thinking about concrete problems (missing implementation details)
- Different moral standards for psychologically near vs distant situations

When construal level IS appropriate:
- The level of abstraction matches the decision stage
- Strategic thinking is appropriately abstract
- Implementation planning is appropriately concrete
- The person can shift between levels as needed
- Distance is acknowledged and compensated for

Output JSON with: construal_level_bias_present (bool), severity (none/mild/moderate/severe), judgment (what is being judged or decided), psychological_distance (what type and degree of distance), current_construal (abstract or concrete), appropriate_construal (what level would be more appropriate), distortion (how is the mismatch affecting judgment), distance_type (temporal/spatial/social/hypothetical), recommendation (construal_appropriate/mild_level_mismatch/significant_construal_bias/major_abstraction_distortion/adjust_construal_level)."""

CONSTRUAL_LEVEL_PROMPT = """Detect construal level bias:

Judgment: {judgment}
Distance: {distance}
Abstraction level: {abstraction}
Decision stage: {stage}
Domain: {domain}
Context: {context}

Is psychological distance causing inappropriate abstraction or concreteness? Return ONLY valid JSON."""


class ConstrualLevelService:
    """Detects construal level bias — distance distorting abstraction level."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        distance: str = "",
        abstraction: str = "",
        stage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect construal level bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONSTRUAL_LEVEL_PROMPT.format(
                judgment=judgment,
                distance=distance or "Not specified",
                abstraction=abstraction or "Not specified",
                stage=stage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONSTRUAL_LEVEL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "construal_level_bias_present": data.get("construal_level_bias_present", False),
            "severity": data.get("severity", ""),
            "psychological_distance": data.get("psychological_distance", ""),
            "current_construal": data.get("current_construal", ""),
            "appropriate_construal": data.get("appropriate_construal", ""),
            "distortion": data.get("distortion", ""),
            "distance_type": data.get("distance_type", ""),
            "recommendation": data.get("recommendation", ""),
        }
