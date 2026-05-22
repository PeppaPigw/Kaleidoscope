"""TestingEffectService — Testing Effect Neglect Detection.

Detects testing effect neglect — failure to use retrieval
practice as a learning strategy, instead relying on passive
review. Roediger & Karpicke (2006). Testing yourself is
far more effective than re-reading, but people consistently
choose re-reading because it feels easier and creates an
illusion of fluency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TESTING_EFFECT_SYSTEM = """You are a testing effect specialist. Given a learning or knowledge verification situation, assess whether passive review is being used when active retrieval would be more effective:

Key concepts (Roediger & Karpicke, 2006):
- Testing effect: retrieval practice enhances long-term retention
- Fluency illusion: re-reading feels effective but isn't
- Desirable difficulties: harder learning = better retention
- Metacognitive failure: people choose ineffective strategies
- Recognition vs recall: recognizing ≠ being able to retrieve
- Spacing effect interaction: spaced retrieval > massed review
- Elaborative retrieval: generating connections during recall

When testing effect neglect IS present:
- Relying on re-reading instead of self-testing
- "I've reviewed it many times" without testing recall
- Confusing recognition with knowledge
- Choosing easy review over effortful retrieval
- "I know this material" based on familiarity, not recall ability
- Passive consumption of information without active engagement
- Avoiding testing because it reveals gaps (feels bad)

When the approach IS appropriate:
- Initial encoding phase where material is new
- The person is using active retrieval strategies
- Testing is being used alongside review
- The person accurately assesses their knowledge level
- The learning strategy matches the retention goal

Output JSON with: testing_effect_neglect_present (bool), severity (none/mild/moderate/severe), situation (what learning situation is occurring), strategy_used (what learning strategy is being used), retrieval_practice (is active retrieval being used?), fluency_illusion (is familiarity being confused with knowledge?), knowledge_assessment (how is knowledge being assessed), effective_alternative (what would be more effective), recommendation (strategy_appropriate/mild_neglect/significant_passive_review/major_testing_neglect/implement_retrieval_practice)."""

TESTING_EFFECT_PROMPT = """Detect testing effect neglect:

Situation: {situation}
Strategy: {strategy}
Assessment: {assessment}
Goal: {goal}
Domain: {domain}
Context: {context}

Is passive review being used when active retrieval would be more effective? Return ONLY valid JSON."""


class TestingEffectService:
    """Detects testing effect neglect — passive review instead of active retrieval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        strategy: str = "",
        assessment: str = "",
        goal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect testing effect neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TESTING_EFFECT_PROMPT.format(
                situation=situation,
                strategy=strategy or "Not specified",
                assessment=assessment or "Not specified",
                goal=goal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TESTING_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "testing_effect_neglect_present": data.get("testing_effect_neglect_present", False),
            "severity": data.get("severity", ""),
            "strategy_used": data.get("strategy_used", ""),
            "retrieval_practice": data.get("retrieval_practice", ""),
            "fluency_illusion": data.get("fluency_illusion", ""),
            "knowledge_assessment": data.get("knowledge_assessment", ""),
            "effective_alternative": data.get("effective_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
