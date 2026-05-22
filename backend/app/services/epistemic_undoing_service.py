"""EpistemicUndoingService — Epistemic Undoing Detection.

Detects epistemic undoing — attempting to reverse or negate a threatening
intellectual insight through symbolic counter-actions or rituals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_UNDOING_SYSTEM = """You are an epistemic undoing specialist. Given attempts to reverse threatening insights, assess undoing:

Key concepts:
- Epistemic undoing: attempting to reverse threatening insight
- Symbolic reversal: counter-action to negate realization
- Ritual behavior: repetitive acts to undo knowledge
- Magical thinking: believing actions can erase understanding
- Compulsive correction: driven to fix what was learned
- Guilt-driven: undoing motivated by guilt about knowing
- Futility: cannot actually unknow what was learned

When epistemic undoing IS present:
- Attempting to reverse insight
- Counter-actions to negate
- Repetitive undoing acts
- Believing can erase understanding
- Driven to fix knowledge
- Guilt about knowing
- Cannot actually unknow

When no undoing:
- Accepting insights
- No counter-actions
- No repetitive acts
- Accepting understanding
- At peace with knowledge
- No guilt about knowing
- Integrating learning

Output JSON with: undoing_detected (bool), severity (none/mild/moderate/severe), reversal_attempt (what counter-action), ritual_pattern (what repetitive), magical_thinking (what believing erase), guilt_driver (what guilt), recommendation (no_undoing/mild_acceptance_practice/significant_integration_therapy/major_intensive_treatment/emergency_compulsive_undoing)."""

EPISTEMIC_UNDOING_PROMPT = """Detect epistemic undoing:

Reversal attempt: {reversal_attempt}
Ritual pattern: {ritual_pattern}
Magical thinking: {magical_thinking}
Guilt driver: {guilt_driver}
Domain: {domain}
Context: {context}

Is there attempt to reverse or negate threatening intellectual insight through counter-actions? Return ONLY valid JSON."""


class EpistemicUndoingService:
    """Detects epistemic undoing — attempting to reverse threatening insights."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reversal_attempt: str,
        *,
        ritual_pattern: str = "",
        magical_thinking: str = "",
        guilt_driver: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic undoing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_UNDOING_PROMPT.format(
                reversal_attempt=reversal_attempt,
                ritual_pattern=ritual_pattern or "Not specified",
                magical_thinking=magical_thinking or "Not specified",
                guilt_driver=guilt_driver or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_UNDOING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reversal_attempt": reversal_attempt[:200],
            "undoing_detected": data.get("undoing_detected", False),
            "severity": data.get("severity", ""),
            "ritual_pattern": data.get("ritual_pattern", ""),
            "magical_thinking": data.get("magical_thinking", ""),
            "guilt_driver": data.get("guilt_driver", ""),
            "recommendation": data.get("recommendation", ""),
        }
