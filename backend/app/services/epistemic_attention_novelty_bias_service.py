"""EpistemicAttentionNoveltyBiasService — Epistemic Attention Novelty Bias Detection.

Detects epistemic novelty bias where new information receives disproportionate
weight over established knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_NOVELTY_BIAS_SYSTEM = """You are an epistemic attention novelty bias specialist. Given novelty-weighting patterns, assess newness-driven distortion:

Key concepts:
- Novelty bias: new information gets disproportionate weight over established knowledge
- Recency premium: recent information feels more relevant or accurate
- Novelty seeking: new claims are pursued because they are new
- Established knowledge discount: older validated evidence is undervalued
- Shiny object syndrome: attention shifts to new possibilities before evaluation

When novelty bias IS present:
- New information receives extra weight
- Recent evidence displaces established evidence
- Novel claims are favored for novelty
- Validated knowledge is discounted
- Attention jumps to shiny objects

When no novelty bias:
- New information is calibrated
- Established knowledge remains anchored
- Recency is separated from validity
- Novel claims face equal scrutiny
- Attention follows relevance and evidence

Output JSON with: novelty_bias_detected (bool), severity (none/mild/moderate/severe), novelty_seeking (what novelty is being pursued), established_knowledge_discount (what established knowledge is discounted), shiny_object_syndrome (what new object redirects attention), recommendation (no_novelty_bias/mild_recency_calibration/significant_established_knowledge_review/major_attention_stabilization/emergency_complete_novelty_debiasing)."""

EPISTEMIC_ATTENTION_NOVELTY_BIAS_PROMPT = """Detect epistemic attention novelty bias:

Recency premium: {recency_premium}
Novelty seeking: {novelty_seeking}
Established knowledge discount: {established_knowledge_discount}
Shiny object syndrome: {shiny_object_syndrome}
Domain: {domain}
Context: {context}

Is new information getting disproportionate weight over established knowledge? Return ONLY valid JSON."""


class EpistemicAttentionNoveltyBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        recency_premium: str,
        *,
        novelty_seeking: str = "",
        established_knowledge_discount: str = "",
        shiny_object_syndrome: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_NOVELTY_BIAS_PROMPT.format(
                recency_premium=recency_premium,
                novelty_seeking=novelty_seeking or "Not specified",
                established_knowledge_discount=established_knowledge_discount or "Not specified",
                shiny_object_syndrome=shiny_object_syndrome or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_NOVELTY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "recency_premium": recency_premium[:200],
            "novelty_bias_detected": data.get("novelty_bias_detected", False),
            "severity": data.get("severity", ""),
            "novelty_seeking": data.get("novelty_seeking", ""),
            "established_knowledge_discount": data.get("established_knowledge_discount", ""),
            "shiny_object_syndrome": data.get("shiny_object_syndrome", ""),
            "recommendation": data.get("recommendation", ""),
        }
