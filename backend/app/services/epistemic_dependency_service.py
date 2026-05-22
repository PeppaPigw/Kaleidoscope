"""EpistemicDependencyService — Epistemic Dependency Detection.

Detects epistemic dependency — unhealthy dependence on others for
all epistemic work, failing to develop one's own epistemic capacities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEPENDENCY_SYSTEM = """You are an epistemic dependency specialist. Given a knowledge-seeking pattern, assess whether unhealthy epistemic dependence exists:

Key concepts:
- Epistemic dependency: unhealthy dependence on others for epistemic work
- Thinking outsourcing: outsourcing all thinking to others
- Judgment delegation: delegating all judgment without engagement
- Epistemic helplessness: learned helplessness in epistemic matters
- Authority reliance: excessive reliance on authority for all beliefs
- Capacity atrophy: epistemic capacities atrophying from disuse
- Self-trust deficit: lacking trust in own epistemic abilities

When epistemic dependency IS present:
- Unhealthy dependence on others for all epistemic work
- All thinking outsourced without engagement
- Judgment delegated without developing own
- Learned helplessness in epistemic matters
- Excessive reliance on authority for all beliefs
- Own epistemic capacities atrophying
- No trust in own epistemic abilities

When appropriate reliance is present:
- Reliance on others proportionate and selective
- Thinking engaged with even when consulting others
- Judgment developed alongside expert consultation
- Epistemic confidence appropriate to competence
- Authority consulted while maintaining own judgment
- Own capacities developed and maintained
- Self-trust balanced with appropriate humility

Output JSON with: dependency_present (bool), severity (none/mild/moderate/severe), pattern (what dependency pattern exists), reliance (what reliance exists), own_capacity (what own capacity exists), atrophy (what atrophy occurs), recommendation (appropriate_reliance/mild_dependency/significant_epistemic_dependency/major_capacity_atrophy/develop_epistemic_autonomy)."""

EPISTEMIC_DEPENDENCY_PROMPT = """Detect epistemic dependency:

Pattern: {pattern}
Reliance: {reliance}
Own capacity: {capacity}
Development: {development}
Domain: {domain}
Context: {context}

Is there unhealthy dependence on others for epistemic work? Return ONLY valid JSON."""


class EpistemicDependencyService:
    """Detects epistemic dependency — unhealthy dependence on others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        reliance: str = "",
        capacity: str = "",
        development: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dependency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEPENDENCY_PROMPT.format(
                pattern=pattern,
                reliance=reliance or "Not specified",
                capacity=capacity or "Not specified",
                development=development or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEPENDENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "dependency_present": data.get("dependency_present", False),
            "severity": data.get("severity", ""),
            "reliance": data.get("reliance", ""),
            "own_capacity": data.get("own_capacity", ""),
            "atrophy": data.get("atrophy", ""),
            "recommendation": data.get("recommendation", ""),
        }
