"""EpistemicSocialComparisonService — Epistemic Social Comparison Detection.

Detects epistemic social comparison — comparing knowledge and beliefs
to others and adjusting based on comparison rather than evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_COMPARISON_SYSTEM = """You are an epistemic social comparison specialist. Given comparing knowledge to others and adjusting, assess social comparison:

Key concepts:
- Epistemic social comparison: comparing knowledge/beliefs to others and adjusting
- Upward comparison: feeling inadequate compared to more knowledgeable others
- Downward comparison: feeling superior compared to less knowledgeable others
- Knowledge jealousy: jealous of others' knowledge leading to distortion
- Expertise comparison: comparing expertise levels and adjusting claims
- Belief benchmarking: benchmarking beliefs against others rather than evidence
- Intellectual ranking: ranking self intellectually and adjusting accordingly

When epistemic social comparison IS present:
- Comparing and adjusting beliefs
- Feeling inadequate upward
- Feeling superior downward
- Knowledge jealousy active
- Expertise compared and claims adjusted
- Beliefs benchmarked against others
- Intellectual ranking affecting beliefs

When no social comparison:
- Beliefs held on own merits
- No inadequacy from comparison
- No superiority from comparison
- No knowledge jealousy
- Expertise assessed independently
- Beliefs based on evidence
- No ranking affecting beliefs

Output JSON with: social_comparison_detected (bool), severity (none/mild/moderate/severe), upward_comparison (what feeling inadequate about), downward_comparison (what feeling superior about), knowledge_jealousy (what jealous about), belief_benchmarking (what beliefs benchmarked against others), recommendation (no_social_comparison/mild_independence_practice/significant_self_reference_recovery/major_intensive_autonomy_building/emergency_complete_social_comparison)."""

EPISTEMIC_SOCIAL_COMPARISON_PROMPT = """Detect epistemic social comparison:

Upward comparison: {upward_comparison}
Downward comparison: {downward_comparison}
Knowledge jealousy: {knowledge_jealousy}
Belief benchmarking: {belief_benchmarking}
Domain: {domain}
Context: {context}

Are beliefs being adjusted based on comparison to others rather than evidence? Return ONLY valid JSON."""


class EpistemicSocialComparisonService:
    """Detects epistemic social comparison — comparing and adjusting beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        upward_comparison: str,
        *,
        downward_comparison: str = "",
        knowledge_jealousy: str = "",
        belief_benchmarking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic social comparison."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_COMPARISON_PROMPT.format(
                upward_comparison=upward_comparison,
                downward_comparison=downward_comparison or "Not specified",
                knowledge_jealousy=knowledge_jealousy or "Not specified",
                belief_benchmarking=belief_benchmarking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_COMPARISON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "upward_comparison": upward_comparison[:200],
            "social_comparison_detected": data.get("social_comparison_detected", False),
            "severity": data.get("severity", ""),
            "downward_comparison": data.get("downward_comparison", ""),
            "knowledge_jealousy": data.get("knowledge_jealousy", ""),
            "belief_benchmarking": data.get("belief_benchmarking", ""),
            "recommendation": data.get("recommendation", ""),
        }
