"""EpistemicEcologyAttentionEconomyService - Attention Economy Distortion Detection.

Detects attention economy distortions where engagement metrics override truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECOLOGY_ATTENTION_ECONOMY_SYSTEM = """You are an epistemic ecology attention economy specialist. Given engagement-over-accuracy dynamics, assess whether engagement metrics override truth:

Key concepts:
- Attention economy distortion: truth-seeking degraded by competition for attention
- Engagement over accuracy: optimizing attention metrics instead of reliability
- Outrage optimization: provoking anger or conflict to capture attention
- Clickbait epistemology: claims shaped for clicks rather than truth
- Depth sacrifice: nuance and depth sacrificed for engagement

When attention economy distortion IS present:
- Engagement metrics override accuracy
- Outrage is optimized over understanding
- Claims are clickbaited into epistemic distortion
- Depth and nuance are sacrificed
- Truth-seeking is subordinated to attention capture

When no attention economy distortion:
- Accuracy remains more important than engagement
- Attention is earned without outrage optimization
- Claims are framed for clarity rather than clicks
- Depth is preserved where needed
- Truth-seeking constrains attention incentives

Output JSON with: distortion_detected (bool), severity (none/mild/moderate/severe), outrage_optimization (how outrage is optimized), clickbait_epistemology (how claims are distorted for clicks), depth_sacrifice (what depth is sacrificed), recommendation (no_distortion/mild_metric_rebalancing/significant_accuracy_restoration/major_attention_incentive_reform/emergency_truth_alignment)."""

EPISTEMIC_ECOLOGY_ATTENTION_ECONOMY_PROMPT = """Detect epistemic ecology attention economy distortion:

Engagement over accuracy: {engagement_over_accuracy}
Outrage optimization: {outrage_optimization}
Clickbait epistemology: {clickbait_epistemology}
Depth sacrifice: {depth_sacrifice}
Domain: {domain}
Context: {context}

Are engagement metrics overriding truth? Return ONLY valid JSON."""


class EpistemicEcologyAttentionEconomyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        engagement_over_accuracy: str,
        *,
        outrage_optimization: str = "",
        clickbait_epistemology: str = "",
        depth_sacrifice: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECOLOGY_ATTENTION_ECONOMY_PROMPT.format(
                engagement_over_accuracy=engagement_over_accuracy,
                outrage_optimization=outrage_optimization or "Not specified",
                clickbait_epistemology=clickbait_epistemology or "Not specified",
                depth_sacrifice=depth_sacrifice or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECOLOGY_ATTENTION_ECONOMY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "engagement_over_accuracy": engagement_over_accuracy[:200],
            "distortion_detected": data.get("distortion_detected", False),
            "severity": data.get("severity", ""),
            "outrage_optimization": data.get("outrage_optimization", ""),
            "clickbait_epistemology": data.get("clickbait_epistemology", ""),
            "depth_sacrifice": data.get("depth_sacrifice", ""),
            "recommendation": data.get("recommendation", ""),
        }
