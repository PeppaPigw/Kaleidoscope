"""EpistemicIntellectualDependencyService — Epistemic Intellectual Dependency Detection.

Detects epistemic intellectual dependency — depending on another person
to do one's thinking rather than developing independent thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INTELLECTUAL_DEPENDENCY_SYSTEM = """You are an epistemic intellectual dependency specialist. Given depending on others to think, assess intellectual dependency:

Key concepts:
- Epistemic intellectual dependency: depending on another to do one's thinking
- Thought outsourcing: letting someone else think for you
- Intellectual learned helplessness: believing one cannot think independently
- Authority reliance: needing authority figures to form opinions
- Cognitive delegation: delegating all cognitive work to others
- Independent thought atrophy: losing ability to think independently
- Intellectual crutch: using another person as intellectual crutch

When epistemic intellectual dependency IS present:
- Depending on another to think
- Letting someone else think for you
- Believing cannot think independently
- Needing authority to form opinions
- Delegating all cognitive work
- Losing independent thought ability
- Using others as intellectual crutch

When no intellectual dependency:
- Thinking independently
- Forming own opinions
- Confident in own reasoning
- Using authorities as input not replacement
- Doing own cognitive work
- Strong independent thought
- Self-sufficient intellectually

Output JSON with: intellectual_dependency_detected (bool), severity (none/mild/moderate/severe), thought_outsourcing (who thinking outsourced to), authority_reliance (what authorities relied on), independent_thought_atrophy (what independent capacity lost), intellectual_crutch (who used as crutch), recommendation (no_intellectual_dependency/mild_independence_practice/significant_autonomy_building/major_intensive_self_reliance/emergency_complete_intellectual_dependency)."""

EPISTEMIC_INTELLECTUAL_DEPENDENCY_PROMPT = """Detect epistemic intellectual dependency:

Thought outsourcing: {thought_outsourcing}
Authority reliance: {authority_reliance}
Independent thought atrophy: {independent_thought_atrophy}
Intellectual crutch: {intellectual_crutch}
Domain: {domain}
Context: {context}

Is there depending on another person to do one's thinking? Return ONLY valid JSON."""


class EpistemicIntellectualDependencyService:
    """Detects epistemic intellectual dependency — depending on another to think."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        thought_outsourcing: str,
        *,
        authority_reliance: str = "",
        independent_thought_atrophy: str = "",
        intellectual_crutch: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic intellectual dependency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INTELLECTUAL_DEPENDENCY_PROMPT.format(
                thought_outsourcing=thought_outsourcing,
                authority_reliance=authority_reliance or "Not specified",
                independent_thought_atrophy=independent_thought_atrophy or "Not specified",
                intellectual_crutch=intellectual_crutch or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INTELLECTUAL_DEPENDENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thought_outsourcing": thought_outsourcing[:200],
            "intellectual_dependency_detected": data.get("intellectual_dependency_detected", False),
            "severity": data.get("severity", ""),
            "authority_reliance": data.get("authority_reliance", ""),
            "independent_thought_atrophy": data.get("independent_thought_atrophy", ""),
            "intellectual_crutch": data.get("intellectual_crutch", ""),
            "recommendation": data.get("recommendation", ""),
        }
