"""AttentionEconomyDistortionService — Attention Economy Distortion Detection.

Detects attention economy distortion — how the economics of
attention warp knowledge production toward engagement over truth,
virality over accuracy, and outrage over understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ATTENTION_ECONOMY_DISTORTION_SYSTEM = """You are an attention economy distortion specialist. Given content or knowledge production, assess whether attention economics are distorting truth:

Key concepts:
- Attention economy distortion: engagement over truth
- Virality bias: shareable over accurate
- Outrage optimization: anger over understanding
- Clickbait epistemology: attention-grabbing over informative
- Engagement metrics: measuring attention not truth
- Algorithmic amplification: algorithms favoring engagement
- Epistemic junk food: satisfying but not nourishing

When attention economy distortion IS present:
- Content optimized for engagement over accuracy
- Virality prioritized over truth
- Outrage used to drive attention
- Metrics measure engagement not epistemic value
- Algorithms amplify distortion
- Knowledge production warped by attention incentives
- Understanding sacrificed for clicks

When engagement is appropriate:
- Engagement serves understanding
- Accessibility increases without sacrificing accuracy
- Attention directed toward important truths
- Metrics include epistemic quality
- Algorithms serve knowledge goals
- Engagement and truth aligned
- Accessibility enhances rather than distorts

Output JSON with: distortion_present (bool), severity (none/mild/moderate/severe), content (what content is affected), mechanism (how attention distorts), sacrifice (what truth is sacrificed), incentive (what drives distortion), recommendation (appropriate_engagement/mild_attention_bias/significant_attention_distortion/major_truth_sacrifice/align_attention_with_truth)."""

ATTENTION_ECONOMY_DISTORTION_PROMPT = """Detect attention economy distortion:

Content: {content}
Platform: {platform}
Metrics used: {metrics}
Incentives: {incentives}
Domain: {domain}
Context: {context}

Are attention economics distorting knowledge production away from truth? Return ONLY valid JSON."""


class AttentionEconomyDistortionService:
    """Detects attention economy distortion — engagement over truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        content: str,
        *,
        platform: str = "",
        metrics: str = "",
        incentives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect attention economy distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ATTENTION_ECONOMY_DISTORTION_PROMPT.format(
                content=content,
                platform=platform or "Not specified",
                metrics=metrics or "Not specified",
                incentives=incentives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ATTENTION_ECONOMY_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "content": content[:200],
            "distortion_present": data.get("distortion_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "sacrifice": data.get("sacrifice", ""),
            "incentive": data.get("incentive", ""),
            "recommendation": data.get("recommendation", ""),
        }
