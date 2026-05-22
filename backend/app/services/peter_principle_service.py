"""PeterPrincipleService — Peter Principle Detection.

Detects the Peter Principle — people in hierarchies rise to their
level of incompetence because promotion is based on current-role
performance rather than next-role capability. A great engineer
becomes a mediocre manager. The system fills every position with
someone unqualified for it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PETER_SYSTEM = """You are a Peter Principle specialist. Given an organizational situation, assess whether the Peter Principle is at play:

Key concepts (Laurence Peter, 1969):
- Promotion based on current performance, not future-role capability
- Each person rises until they reach a role they can't perform well
- The system eventually fills every position with someone incompetent at it
- "The cream rises until it sours"
- Work gets done by those who haven't yet reached their level of incompetence

Related concepts:
- Dilbert Principle: incompetent workers promoted to management to limit damage
- Putt's Law: technology is dominated by two types — those who understand what they don't manage, and those who manage what they don't understand
- Skill mismatch: the skills that got you promoted aren't the skills you need in the new role

Output JSON with: peter_principle_present (bool), severity (none/mild/moderate/severe/systemic), role_transition (what role change occurred or is proposed), previous_role_competence (how well they performed in prior role), current_role_competence (how well they perform in current role), skill_mismatch (what skills are needed vs what skills they have), promotion_basis (what the promotion was based on), role_requirements (what the new role actually requires), competence_gap (what capabilities are missing), organizational_impact (how the mismatch affects the organization), lateral_move_option (could they be effective in a different role at same level?), training_feasible (could the gap be closed with development?), who_suffers (who is affected by the incompetence), systemic_pattern (bool — is this happening across the organization?), alternative_reward (how to reward performance without promoting to incompetence), recommendation (promotion_appropriate/mild_stretch/significant_mismatch/classic_peter_principle/systemic_problem)."""

PETER_PROMPT = """Detect Peter Principle:

Situation: {situation}
Role transition: {transition}
Performance history: {performance}
New role requirements: {requirements}
Domain: {domain}
Context: {context}

Is the Peter Principle at play? Return ONLY valid JSON."""


class PeterPrincipleService:
    """Detects Peter Principle — promotion to incompetence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        transition: str = "",
        performance: str = "",
        requirements: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Peter Principle."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PETER_PROMPT.format(
                situation=situation,
                transition=transition or "Not specified",
                performance=performance or "Not specified",
                requirements=requirements or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PETER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "peter_principle_present": data.get("peter_principle_present", False),
            "severity": data.get("severity", ""),
            "role_transition": data.get("role_transition", ""),
            "previous_role_competence": data.get("previous_role_competence", ""),
            "current_role_competence": data.get("current_role_competence", ""),
            "skill_mismatch": data.get("skill_mismatch", ""),
            "promotion_basis": data.get("promotion_basis", ""),
            "role_requirements": data.get("role_requirements", ""),
            "competence_gap": data.get("competence_gap", ""),
            "organizational_impact": data.get("organizational_impact", ""),
            "lateral_move_option": data.get("lateral_move_option", ""),
            "training_feasible": data.get("training_feasible", ""),
            "who_suffers": data.get("who_suffers", ""),
            "systemic_pattern": data.get("systemic_pattern", False),
            "alternative_reward": data.get("alternative_reward", ""),
            "recommendation": data.get("recommendation", ""),
        }
