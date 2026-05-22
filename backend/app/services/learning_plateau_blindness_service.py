"""LearningPlateauBlindnessService — Learning Plateau Blindness Detection.

Detects learning plateau blindness — not recognizing when learning
has stalled and new approaches are needed, where continued effort
in the same direction yields diminishing returns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

LEARNING_PLATEAU_BLINDNESS_SYSTEM = """You are a learning plateau blindness specialist. Given a learning or improvement effort, assess whether a plateau is unrecognized:

Key concepts:
- Learning plateau blindness: not seeing when learning has stalled
- Diminishing returns denial: continuing despite no progress
- Effort-progress confusion: effort mistaken for progress
- Method fixation: same method despite no improvement
- Plateau normalization: stagnation treated as acceptable
- Breakthrough avoidance: not seeking new approaches when stuck
- Comfort zone persistence: staying in familiar but unproductive patterns

When plateau blindness IS present:
- Learning or improvement has stalled
- Same methods continued despite no progress
- Effort confused with actual advancement
- Stagnation not recognized as a problem
- New approaches not sought
- Diminishing returns not acknowledged
- Comfort with familiar but unproductive patterns

When continued effort is appropriate:
- Progress still occurring even if slow
- Method still yielding improvements
- Plateau recognized and being addressed
- New approaches being explored
- Diminishing returns acknowledged and managed
- Effort directed at breakthrough strategies
- Stagnation diagnosed and responded to

Output JSON with: plateau_blindness_present (bool), severity (none/mild/moderate/severe), effort (what effort is being made), progress (what progress is occurring), stagnation_signs (signs of plateau), alternative_approaches (what alternatives exist), recommendation (appropriate_persistence/mild_plateau_unawareness/significant_plateau_blindness/major_stagnation_denial/diagnose_plateau_and_change_approach)."""

LEARNING_PLATEAU_BLINDNESS_PROMPT = """Detect learning plateau blindness:

Effort: {effort}
Progress observed: {progress}
Duration: {duration}
Methods used: {methods}
Domain: {domain}
Context: {context}

Is a learning plateau going unrecognized while the same approaches continue? Return ONLY valid JSON."""


class LearningPlateauBlindnessService:
    """Detects learning plateau blindness — unrecognized stagnation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        effort: str,
        *,
        progress: str = "",
        duration: str = "",
        methods: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect learning plateau blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=LEARNING_PLATEAU_BLINDNESS_PROMPT.format(
                effort=effort,
                progress=progress or "Not specified",
                duration=duration or "Not specified",
                methods=methods or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=LEARNING_PLATEAU_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "effort": effort[:200],
            "plateau_blindness_present": data.get("plateau_blindness_present", False),
            "severity": data.get("severity", ""),
            "progress": data.get("progress", ""),
            "stagnation_signs": data.get("stagnation_signs", ""),
            "alternative_approaches": data.get("alternative_approaches", ""),
            "recommendation": data.get("recommendation", ""),
        }
