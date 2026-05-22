"""ChronologicalSnobberyService — Chronological Snobbery Detection.

Detects chronological snobbery — dismissing ideas solely because
they are old, or accepting ideas solely because they are new,
without evaluating their actual epistemic merit.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHRONOLOGICAL_SNOBBERY_SYSTEM = """You are a chronological snobbery specialist. Given an evaluation of ideas, assess whether temporal bias is distorting judgment:

Key concepts:
- Chronological snobbery: dismissing old ideas as outdated
- Neophilia: accepting new ideas uncritically
- Temporal chauvinism: treating one's era as epistemically superior
- Progress assumption: assuming newer means better
- Antiquarianism: treating old as inherently superior
- Temporal context collapse: ignoring historical context
- Whig epistemology: reading history as progress toward present

When chronological snobbery IS present:
- Ideas dismissed solely because of their age
- New ideas accepted without evaluation
- Current era treated as epistemically superior
- Progress assumed without demonstration
- Historical context ignored in evaluation
- Temporal origin used as proxy for quality
- No engagement with actual content of old ideas

When temporal evaluation is appropriate:
- Ideas evaluated on merit regardless of age
- Historical context informs but doesn't determine
- Progress demonstrated not assumed
- Old ideas engaged with substantively
- New ideas scrutinized equally
- Temporal context enriches understanding
- Both old and new judged by evidence

Output JSON with: snobbery_present (bool), severity (none/mild/moderate/severe), evaluation (what is evaluated), temporal_bias (what temporal bias exists), dismissed (what is dismissed due to age), merit (what actual merit exists), recommendation (appropriate_temporal_evaluation/mild_recency_preference/significant_chronological_snobbery/major_temporal_chauvinism/evaluate_on_merit)."""

CHRONOLOGICAL_SNOBBERY_PROMPT = """Detect chronological snobbery:

Evaluation: {evaluation}
Idea age: {age}
Dismissal reason: {reason}
Actual merit: {merit}
Domain: {domain}
Context: {context}

Are ideas being dismissed or accepted based on temporal origin rather than merit? Return ONLY valid JSON."""


class ChronologicalSnobberyService:
    """Detects chronological snobbery — temporal bias in idea evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        age: str = "",
        reason: str = "",
        merit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect chronological snobbery."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHRONOLOGICAL_SNOBBERY_PROMPT.format(
                evaluation=evaluation,
                age=age or "Not specified",
                reason=reason or "Not specified",
                merit=merit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHRONOLOGICAL_SNOBBERY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "snobbery_present": data.get("snobbery_present", False),
            "severity": data.get("severity", ""),
            "temporal_bias": data.get("temporal_bias", ""),
            "dismissed": data.get("dismissed", ""),
            "merit": data.get("merit", ""),
            "recommendation": data.get("recommendation", ""),
        }
