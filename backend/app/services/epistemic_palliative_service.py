"""EpistemicPalliativeService — Epistemic Palliative Care Detection.

Detects need for epistemic palliative care — managing intellectual suffering
when cure is no longer possible, focusing on comfort and dignity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PALLIATIVE_SYSTEM = """You are an epistemic palliative care specialist. Given intellectual suffering beyond cure, assess palliative care need:

Key concepts:
- Epistemic palliative: comfort care when cure impossible
- Symptom management: controlling intellectual suffering
- Goals of care: what outcomes are realistic
- Comfort measures: prioritizing ease over cure
- Dignity preservation: maintaining intellectual worth
- Hospice transition: accepting terminal intellectual state
- Quality of life: maximizing remaining function

When epistemic palliative care IS needed:
- Intellectual condition beyond cure
- Suffering requiring management
- Unrealistic curative goals
- Need for comfort prioritization
- Dignity at risk of loss
- Terminal intellectual state present
- Quality of remaining function declining

When no palliative care needed:
- Curative options available
- No significant suffering
- Realistic recovery goals
- Normal function maintained
- Dignity intact
- Non-terminal state
- Good quality of function

Output JSON with: palliative_needed (bool), severity (none/mild/moderate/severe), suffering_type (what distress), goals_of_care (what realistic outcomes), comfort_measures (what ease interventions), dignity_status (what worth preservation), recommendation (no_palliative_needed/mild_comfort/significant_palliative/major_hospice/transition_to_comfort_only)."""

EPISTEMIC_PALLIATIVE_PROMPT = """Detect epistemic palliative care need:

Suffering type: {suffering_type}
Goals of care: {goals_of_care}
Comfort measures: {comfort_measures}
Dignity status: {dignity_status}
Domain: {domain}
Context: {context}

Is the intellectual condition beyond cure and requiring comfort-focused care? Return ONLY valid JSON."""


class EpistemicPalliativeService:
    """Detects epistemic palliative care need — comfort when cure impossible."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        suffering_type: str,
        *,
        goals_of_care: str = "",
        comfort_measures: str = "",
        dignity_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic palliative care need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PALLIATIVE_PROMPT.format(
                suffering_type=suffering_type,
                goals_of_care=goals_of_care or "Not specified",
                comfort_measures=comfort_measures or "Not specified",
                dignity_status=dignity_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PALLIATIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "suffering_type": suffering_type[:200],
            "palliative_needed": data.get("palliative_needed", False),
            "severity": data.get("severity", ""),
            "goals_of_care": data.get("goals_of_care", ""),
            "comfort_measures": data.get("comfort_measures", ""),
            "dignity_status": data.get("dignity_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
