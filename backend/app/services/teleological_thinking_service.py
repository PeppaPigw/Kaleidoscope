"""TeleologicalThinkingService — Teleological Thinking Detection.

Detects teleological thinking — assuming events happened for a
purpose or toward a goal, imposing intentionality on processes
that are actually purposeless or emergent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TELEOLOGICAL_THINKING_SYSTEM = """You are a teleological thinking specialist. Given an explanation, assess whether purposeless processes are being described as goal-directed:

Key concepts:
- Teleology: explanation by purpose or final cause
- Promiscuous teleology: seeing purpose where none exists
- Design inference: assuming design without evidence
- Functional explanation: describing what something does vs why it exists
- Adaptationism: assuming every feature has a purpose
- Anthropomorphism: attributing human intentions to non-human processes
- Emergent vs designed: outcomes from process vs outcomes from planning

When teleological thinking IS present:
- Purposeless processes described as goal-directed
- Natural selection described as "designing" or "intending"
- Market outcomes described as "meant to be"
- Historical events described as "leading to" a purpose
- Evolution described as progressive or goal-directed
- Emergent outcomes attributed to planning or intention
- "Everything happens for a reason" applied to random events

When teleological language is appropriate:
- Describing actual intentional agents and their goals
- Using functional language as shorthand (acknowledged)
- Discussing genuinely designed systems
- Describing goal-directed behavior of conscious agents
- Using teleological language metaphorically (flagged as such)
- Discussing systems with actual feedback toward goals
- Engineering contexts where design is literal

Output JSON with: teleological_present (bool), severity (none/mild/moderate/severe), explanation (what is being explained), purpose_attributed (what purpose is claimed), actual_process (what the actual mechanism is), anthropomorphism (what human qualities are projected), recommendation (appropriate_teleology/mild_purpose_language/significant_teleological_thinking/major_purpose_imposition/describe_mechanism_not_purpose)."""

TELEOLOGICAL_THINKING_PROMPT = """Detect teleological thinking:

Explanation: {explanation}
Process described: {process}
Purpose claimed: {purpose}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Are purposeless processes being described as goal-directed? Return ONLY valid JSON."""


class TeleologicalThinkingService:
    """Detects teleological thinking — imposing purpose on purposeless processes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        process: str = "",
        purpose: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect teleological thinking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TELEOLOGICAL_THINKING_PROMPT.format(
                explanation=explanation,
                process=process or "Not specified",
                purpose=purpose or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TELEOLOGICAL_THINKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "teleological_present": data.get("teleological_present", False),
            "severity": data.get("severity", ""),
            "purpose_attributed": data.get("purpose_attributed", ""),
            "actual_process": data.get("actual_process", ""),
            "anthropomorphism": data.get("anthropomorphism", ""),
            "recommendation": data.get("recommendation", ""),
        }
