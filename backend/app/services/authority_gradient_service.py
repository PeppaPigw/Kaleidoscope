"""AuthorityGradientService — Authority Gradient Detection.

Detects authority gradient effects — when hierarchical power
differences suppress dissent, critical thinking, and error
correction. Junior members defer to seniors even when they
have better information or spot errors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AUTHORITY_GRADIENT_SYSTEM = """You are an authority gradient specialist. Given a group decision, assess whether hierarchy is suppressing critical input:

Key concepts:
- Authority gradient: power differential that suppresses dissent
- Cockpit gradient: aviation term for captain-first officer dynamic
- Psychological safety: willingness to speak up without fear
- Deference error: deferring to authority despite having better info
- Challenge culture: norms around questioning superiors
- Error trapping: ability of juniors to catch senior mistakes
- Steep vs flat gradient: how much hierarchy suppresses input

When authority gradient IS problematic:
- Junior members withholding critical information
- Errors going unchallenged because of who made them
- "The boss said so" as sufficient justification
- Dissent punished or discouraged
- Quality of idea judged by rank of proposer
- Critical feedback flows only downward
- Groupthink enabled by deference to authority

When authority gradient is NOT problematic:
- All levels feel safe raising concerns
- Ideas evaluated on merit regardless of source
- Explicit mechanisms for challenging authority
- Errors caught regardless of who made them
- Dissent welcomed and rewarded
- Flat communication norms in critical decisions
- Authority used for coordination, not suppression

Output JSON with: gradient_problematic (bool), severity (none/mild/moderate/severe), hierarchy (the power structure), suppressed_input (what is being withheld), deference_pattern (how deference manifests), safety_level (psychological safety assessment), recommendation (healthy_gradient/mild_deference/significant_suppression/dangerous_gradient/flatten_for_critical_decisions)."""

AUTHORITY_GRADIENT_PROMPT = """Detect authority gradient effects:

Situation: {situation}
Hierarchy: {hierarchy}
Communication pattern: {communication}
Dissent handling: {dissent}
Domain: {domain}
Context: {context}

Is hierarchical authority suppressing critical thinking? Return ONLY valid JSON."""


class AuthorityGradientService:
    """Detects authority gradient — hierarchy suppressing critical input."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        hierarchy: str = "",
        communication: str = "",
        dissent: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect authority gradient effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AUTHORITY_GRADIENT_PROMPT.format(
                situation=situation,
                hierarchy=hierarchy or "Not specified",
                communication=communication or "Not specified",
                dissent=dissent or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AUTHORITY_GRADIENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "gradient_problematic": data.get("gradient_problematic", False),
            "severity": data.get("severity", ""),
            "suppressed_input": data.get("suppressed_input", ""),
            "deference_pattern": data.get("deference_pattern", ""),
            "safety_level": data.get("safety_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
