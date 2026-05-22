"""EpistemicFutureAnxietyService — Epistemic Future Anxiety Detection.

Detects epistemic future anxiety — anxiety about future knowledge states
paralyzing present inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FUTURE_ANXIETY_SYSTEM = """You are an epistemic future anxiety specialist. Given anxiety about future knowledge, assess future anxiety:

Key concepts:
- Epistemic future anxiety: anxiety about future knowledge paralyzing inquiry
- Obsolescence fear: afraid current knowledge will become worthless
- Uncertainty paralysis: frozen by unknowable future developments
- Knowledge futility: believing learning is pointless since it'll change
- Progress overwhelm: overwhelmed by pace of knowledge change
- Relevance anxiety: worried about staying intellectually relevant
- Future shock: unable to cope with anticipated knowledge shifts

When epistemic future anxiety IS present:
- Anxiety paralyzing inquiry
- Afraid knowledge will become worthless
- Frozen by unknowable future
- Believing learning is pointless
- Overwhelmed by pace of change
- Worried about relevance
- Unable to cope with shifts

When no future anxiety:
- Present inquiry unimpeded
- Confident in current value
- Comfortable with uncertainty
- Learning valued regardless
- Pace manageable
- Secure in relevance
- Adaptable to shifts

Output JSON with: future_anxiety_detected (bool), severity (none/mild/moderate/severe), obsolescence_fear (what afraid will become worthless), uncertainty_paralysis (what frozen by), knowledge_futility (what believing pointless), progress_overwhelm (what overwhelmed by), recommendation (no_future_anxiety/mild_present_grounding/significant_uncertainty_tolerance/major_intensive_adaptability_work/emergency_complete_future_paralysis)."""

EPISTEMIC_FUTURE_ANXIETY_PROMPT = """Detect epistemic future anxiety:

Obsolescence fear: {obsolescence_fear}
Uncertainty paralysis: {uncertainty_paralysis}
Knowledge futility: {knowledge_futility}
Progress overwhelm: {progress_overwhelm}
Domain: {domain}
Context: {context}

Is there anxiety about future knowledge states paralyzing present inquiry? Return ONLY valid JSON."""


class EpistemicFutureAnxietyService:
    """Detects epistemic future anxiety — anxiety about future knowledge paralyzing inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        obsolescence_fear: str,
        *,
        uncertainty_paralysis: str = "",
        knowledge_futility: str = "",
        progress_overwhelm: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic future anxiety."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FUTURE_ANXIETY_PROMPT.format(
                obsolescence_fear=obsolescence_fear,
                uncertainty_paralysis=uncertainty_paralysis or "Not specified",
                knowledge_futility=knowledge_futility or "Not specified",
                progress_overwhelm=progress_overwhelm or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FUTURE_ANXIETY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "obsolescence_fear": obsolescence_fear[:200],
            "future_anxiety_detected": data.get("future_anxiety_detected", False),
            "severity": data.get("severity", ""),
            "uncertainty_paralysis": data.get("uncertainty_paralysis", ""),
            "knowledge_futility": data.get("knowledge_futility", ""),
            "progress_overwhelm": data.get("progress_overwhelm", ""),
            "recommendation": data.get("recommendation", ""),
        }
