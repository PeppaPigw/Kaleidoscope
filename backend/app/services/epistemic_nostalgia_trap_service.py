"""EpistemicNostalgiaTrapService — Epistemic Nostalgia Trap Detection.

Detects epistemic nostalgia trap — romanticizing past knowledge states
and resisting current understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NOSTALGIA_TRAP_SYSTEM = """You are an epistemic nostalgia trap specialist. Given romanticizing past knowledge, assess nostalgia trap:

Key concepts:
- Epistemic nostalgia trap: romanticizing past knowledge states
- Golden age thinking: believing past understanding was superior
- Progress denial: refusing to accept knowledge has advanced
- Tradition worship: valuing old ideas simply because they're old
- Regression desire: wanting to return to simpler understanding
- Modernism rejection: rejecting current knowledge as inferior
- Wisdom idealization: idealizing past thinkers beyond merit

When epistemic nostalgia trap IS present:
- Romanticizing past knowledge
- Believing past was superior
- Refusing to accept progress
- Valuing old because old
- Wanting simpler understanding
- Rejecting current as inferior
- Idealizing past beyond merit

When no nostalgia trap:
- Balanced view of past
- Acknowledging progress
- Accepting advancement
- Evaluating on merit
- Embracing complexity
- Appreciating current knowledge
- Realistic about past

Output JSON with: nostalgia_trap_detected (bool), severity (none/mild/moderate/severe), golden_age_thinking (what believing past superior about), progress_denial (what refusing to accept advanced), tradition_worship (what valuing because old), regression_desire (what wanting simpler about), recommendation (no_nostalgia_trap/mild_present_appreciation/significant_progress_acceptance/major_intensive_temporal_rebalancing/emergency_complete_past_fixation)."""

EPISTEMIC_NOSTALGIA_TRAP_PROMPT = """Detect epistemic nostalgia trap:

Golden age thinking: {golden_age_thinking}
Progress denial: {progress_denial}
Tradition worship: {tradition_worship}
Regression desire: {regression_desire}
Domain: {domain}
Context: {context}

Is there romanticizing past knowledge states and resisting current understanding? Return ONLY valid JSON."""


class EpistemicNostalgiaTrapService:
    """Detects epistemic nostalgia trap — romanticizing past knowledge states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        golden_age_thinking: str,
        *,
        progress_denial: str = "",
        tradition_worship: str = "",
        regression_desire: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic nostalgia trap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NOSTALGIA_TRAP_PROMPT.format(
                golden_age_thinking=golden_age_thinking,
                progress_denial=progress_denial or "Not specified",
                tradition_worship=tradition_worship or "Not specified",
                regression_desire=regression_desire or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NOSTALGIA_TRAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "golden_age_thinking": golden_age_thinking[:200],
            "nostalgia_trap_detected": data.get("nostalgia_trap_detected", False),
            "severity": data.get("severity", ""),
            "progress_denial": data.get("progress_denial", ""),
            "tradition_worship": data.get("tradition_worship", ""),
            "regression_desire": data.get("regression_desire", ""),
            "recommendation": data.get("recommendation", ""),
        }
