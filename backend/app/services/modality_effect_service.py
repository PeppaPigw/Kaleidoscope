"""ModalityEffectService — Modality Effect Detection.

Detects modality effect — differential processing and recall
based on information presentation format (auditory vs visual
vs text). Penney (1989). People process and remember information
differently depending on the modality, and may make poor
decisions when information is presented in a suboptimal format
for the task at hand.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MODALITY_EFFECT_SYSTEM = """You are a modality effect specialist. Given an information processing or decision situation, assess whether the presentation modality is inappropriately influencing evaluation:

Key concepts (Penney, 1989):
- Modality effect: presentation format affects processing and recall
- Auditory recency: spoken information has stronger recency effect
- Visual superiority: images processed faster than text for some tasks
- Dual coding: information in multiple modalities is better retained
- Format-content confusion: judging quality by presentation format
- Medium is the message: format influencing perceived importance
- Channel capacity: different modalities have different bandwidth

When modality effects ARE distorting judgment:
- Preferring information because it was presented visually/verbally
- Dismissing written evidence in favor of spoken testimony
- Overweighting video/audio evidence over equivalent text
- Presentation format influencing perceived credibility
- "Seeing is believing" when the visual is misleading
- Ignoring data because it's in an unfamiliar format
- Confusing production quality with content quality

When modality consideration IS appropriate:
- Choosing the best format for the specific cognitive task
- Recognizing genuine advantages of multimodal presentation
- Using appropriate format for the audience's processing needs
- Acknowledging that some information is genuinely better in certain formats
- Format choice based on task demands, not bias

Output JSON with: modality_effect_present (bool), severity (none/mild/moderate/severe), situation (what information is being processed), modality_used (what format is the information in), modality_bias (how is format influencing judgment), content_quality (actual content quality regardless of format), format_confusion (is format being confused with quality), optimal_modality (what format would be best for this task), recommendation (modality_appropriate/mild_format_bias/significant_modality_effect/major_format_content_confusion/evaluate_content_not_format)."""

MODALITY_EFFECT_PROMPT = """Detect modality effect:

Situation: {situation}
Format: {format}
Content: {content}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is the presentation modality inappropriately influencing how information is evaluated? Return ONLY valid JSON."""


class ModalityEffectService:
    """Detects modality effect — format of presentation distorting evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        format: str = "",
        content: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect modality effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MODALITY_EFFECT_PROMPT.format(
                situation=situation,
                format=format or "Not specified",
                content=content or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MODALITY_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "modality_effect_present": data.get("modality_effect_present", False),
            "severity": data.get("severity", ""),
            "modality_used": data.get("modality_used", ""),
            "modality_bias": data.get("modality_bias", ""),
            "content_quality": data.get("content_quality", ""),
            "format_confusion": data.get("format_confusion", ""),
            "optimal_modality": data.get("optimal_modality", ""),
            "recommendation": data.get("recommendation", ""),
        }
