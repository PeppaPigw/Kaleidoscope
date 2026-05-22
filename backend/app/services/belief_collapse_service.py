"""BeliefCollapseService — Belief Collapse Detection.

Detects belief collapse — premature collapse of possibility space
when beliefs are observed or questioned.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BELIEF_COLLAPSE_SYSTEM = """You are a belief collapse specialist. Given a reasoning situation, assess whether possibility space collapses prematurely when examined:

Key concepts:
- Belief collapse: possibility space collapsing when observed
- Premature certainty: rushing to certainty when questioned
- Observation effect: examining beliefs changes them
- Possibility elimination: eliminating possibilities prematurely
- Defensive crystallization: beliefs hardening when challenged
- Nuance loss: losing nuance under examination
- Binary snap: complex positions snapping to binary when pressed

When belief collapse IS present:
- Possibility space collapses prematurely when examined
- Rushing to certainty when questioned about beliefs
- Examining beliefs causes them to harden
- Possibilities eliminated prematurely under scrutiny
- Beliefs crystallize defensively when challenged
- Nuance lost when position must be stated
- Complex positions snap to binary when pressed

When healthy examination is present:
- Examination deepens understanding of possibilities
- Questioning reveals additional nuance
- Scrutiny maintains or expands possibility space
- Challenge leads to more careful articulation
- Examination preserves complexity
- Stating position maintains nuance
- Pressure reveals rather than eliminates options

Output JSON with: collapse_present (bool), severity (none/mild/moderate/severe), situation (what situation triggers collapse), possibilities_lost (what possibilities are eliminated), trigger (what triggers the collapse), mechanism (how collapse operates), recommendation (healthy_examination/mild_narrowing/significant_collapse/major_premature_certainty/maintain_possibility_space)."""

BELIEF_COLLAPSE_PROMPT = """Detect belief collapse:

Situation: {situation}
Possibilities: {possibilities}
Trigger: {trigger}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Does possibility space collapse prematurely when examined? Return ONLY valid JSON."""


class BeliefCollapseService:
    """Detects belief collapse — premature collapse of possibility space."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        possibilities: str = "",
        trigger: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect belief collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BELIEF_COLLAPSE_PROMPT.format(
                situation=situation,
                possibilities=possibilities or "Not specified",
                trigger=trigger or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BELIEF_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "collapse_present": data.get("collapse_present", False),
            "severity": data.get("severity", ""),
            "possibilities_lost": data.get("possibilities_lost", ""),
            "trigger": data.get("trigger", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
