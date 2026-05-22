"""EpistemicTechnologyPlatformEpistemologyService — Epistemic Technology Platform Epistemology Detection.

Detects epistemic technology platform epistemology — platform affordances
shaping what counts as knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECHNOLOGY_PLATFORM_EPISTEMOLOGY_SYSTEM = """You are an epistemic technology platform epistemology specialist. Given platform constraints, assess how affordances shape what counts as knowledge:

Key concepts:
- Platform epistemology: platform affordances shaping what counts as knowledge
- Platform constraint: interface, ranking, or format limits on knowing
- Format determines content: what can be said shaped by platform form
- Engagement as validity: attention metrics treated as epistemic value
- Virality as truth: spread mistaken for credibility

When platform epistemology IS present:
- Platform constraints define acceptable knowledge
- Format determines what can be expressed
- Engagement becomes a proxy for validity
- Virality becomes a proxy for truth
- Knowledge practices adapt to platform incentives

When no platform epistemology distortion:
- Platform constraints are recognized and bounded
- Format does not determine epistemic substance
- Engagement is not treated as validity
- Virality is not treated as truth
- Knowledge can be evaluated outside platform incentives

Output JSON with: platform_epistemology_detected (bool), severity (none/mild/moderate/severe), format_determines_content (what content is format-shaped), engagement_as_validity (what engagement is treated as validity), virality_as_truth (what virality is treated as truth), recommendation (no_platform_epistemology/mild_affordance_awareness/significant_metric_separation/major_platform_constraint_repair/emergency_epistemic_decoupling)."""

EPISTEMIC_TECHNOLOGY_PLATFORM_EPISTEMOLOGY_PROMPT = """Detect epistemic technology platform epistemology:

Platform constraint: {platform_constraint}
Format determines content: {format_determines_content}
Engagement as validity: {engagement_as_validity}
Virality as truth: {virality_as_truth}
Domain: {domain}
Context: {context}

Are platform affordances shaping what counts as knowledge? Return ONLY valid JSON."""


class EpistemicTechnologyPlatformEpistemologyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        platform_constraint: str,
        *,
        format_determines_content: str = "",
        engagement_as_validity: str = "",
        virality_as_truth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECHNOLOGY_PLATFORM_EPISTEMOLOGY_PROMPT.format(
                platform_constraint=platform_constraint,
                format_determines_content=format_determines_content or "Not specified",
                engagement_as_validity=engagement_as_validity or "Not specified",
                virality_as_truth=virality_as_truth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECHNOLOGY_PLATFORM_EPISTEMOLOGY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "platform_constraint": platform_constraint[:200],
            "platform_epistemology_detected": data.get("platform_epistemology_detected", False),
            "severity": data.get("severity", ""),
            "format_determines_content": data.get("format_determines_content", ""),
            "engagement_as_validity": data.get("engagement_as_validity", ""),
            "virality_as_truth": data.get("virality_as_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }
