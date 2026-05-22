"""AttentionEconomyEpistemicService — Attention Economy Epistemic Detection.

Detects attention economy epistemic distortion — attention economy
dynamics distorting what gets known, where engagement optimization
displaces truth-seeking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ATTENTION_ECONOMY_EPISTEMIC_SYSTEM = """You are an attention economy epistemic specialist. Given an information distribution pattern, assess whether attention economy dynamics are distorting knowledge:

Key concepts:
- Attention economy epistemic: engagement displacing truth
- Clickbait epistemology: attention-grabbing over accurate
- Engagement optimization: optimizing for engagement not truth
- Virality over validity: viral content displacing valid content
- Outrage epistemology: outrage-generating content dominating
- Simplification for engagement: complexity sacrificed for clicks
- Algorithm-driven knowledge: algorithms shaping what is known

When attention economy distortion IS present:
- Engagement metrics driving what gets known
- Attention-grabbing content displacing accurate content
- Virality determining what information spreads
- Outrage-generating content dominating discourse
- Complexity sacrificed for engagement
- Algorithms shaping knowledge distribution
- Truth-seeking displaced by engagement optimization

When attention dynamics are appropriate:
- Engagement aligned with importance
- Popular content also accurate
- Viral spread of genuinely important information
- Emotional engagement serving understanding
- Accessibility not sacrificing accuracy
- Distribution serving knowledge not just attention
- Algorithms supporting rather than distorting knowledge

Output JSON with: distortion_present (bool), severity (none/mild/moderate/severe), pattern (what distribution pattern exists), engagement_driver (what drives engagement), truth_displaced (what truth is displaced), mechanism (how attention economy distorts), recommendation (aligned_engagement/mild_engagement_bias/significant_attention_distortion/major_truth_displacement/decouple_knowledge_from_engagement_metrics)."""

ATTENTION_ECONOMY_EPISTEMIC_PROMPT = """Detect attention economy epistemic distortion:

Distribution pattern: {pattern}
Engagement drivers: {engagement}
Truth displaced: {truth}
Platform dynamics: {platform}
Domain: {domain}
Context: {context}

Are attention economy dynamics distorting what gets known? Return ONLY valid JSON."""


class AttentionEconomyEpistemicService:
    """Detects attention economy epistemic distortion — engagement displacing truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        engagement: str = "",
        truth: str = "",
        platform: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect attention economy epistemic distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ATTENTION_ECONOMY_EPISTEMIC_PROMPT.format(
                pattern=pattern,
                engagement=engagement or "Not specified",
                truth=truth or "Not specified",
                platform=platform or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ATTENTION_ECONOMY_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "distortion_present": data.get("distortion_present", False),
            "severity": data.get("severity", ""),
            "engagement_driver": data.get("engagement_driver", ""),
            "truth_displaced": data.get("truth_displaced", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
