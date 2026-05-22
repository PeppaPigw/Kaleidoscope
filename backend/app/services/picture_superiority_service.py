"""PictureSuperiorityService — Picture Superiority Effect Detection.

Detects picture superiority effect — images being remembered
and weighted more heavily than equivalent textual information.
Paivio (1971), Nelson et al. (1976). Visual evidence feels
more compelling than written evidence of equal quality. A
photograph convinces more than a paragraph describing the
same thing, regardless of actual evidential value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PICTURE_SUPERIORITY_SYSTEM = """You are a picture superiority effect specialist. Given an evidence evaluation or decision situation, assess whether visual format is being given undue weight over equivalent textual information:

Key concepts (Paivio, 1971; Nelson et al., 1976):
- Picture superiority: images recalled better than words
- Dual coding: images encoded both visually and verbally
- Vividness effect: concrete images more persuasive than abstract text
- Seeing is believing: visual evidence feels more real
- Imageability bias: preferring evidence that can be visualized
- Data visualization effect: charts more persuasive than tables
- Photo evidence premium: photographs weighted over descriptions

When picture superiority IS distorting:
- Giving more weight to photographic evidence over equally valid text
- Charts/graphs being more persuasive than the underlying numbers warrant
- "I saw it with my own eyes" trumping statistical evidence
- Visual presentations winning over better-reasoned text arguments
- Infographics being more convincing than peer-reviewed papers
- Video testimony weighted more than written testimony of equal quality
- Preferring visual proof when textual evidence is equally strong

When visual weighting IS appropriate:
- The visual genuinely reveals something text cannot convey
- Spatial relationships are central to the argument
- The image provides evidence that text merely describes
- Visual pattern recognition is the appropriate analytical tool
- The visual format genuinely aids comprehension of complex data

Output JSON with: picture_superiority_present (bool), severity (none/mild/moderate/severe), situation (what is being evaluated), visual_evidence (what visual information is being weighted), textual_evidence (what textual information is being underweighted), format_bias (how is format affecting credibility), actual_quality (relative quality regardless of format), vividness_effect (is vividness driving persuasion), recommendation (visual_weighting_appropriate/mild_format_bias/significant_picture_superiority/major_visual_over_textual/evaluate_content_not_format)."""

PICTURE_SUPERIORITY_PROMPT = """Detect picture superiority effect:

Situation: {situation}
Visual evidence: {visual}
Text evidence: {textual}
Weighting: {weighting}
Domain: {domain}
Context: {context}

Is visual format causing information to be weighted more heavily than equivalent textual information? Return ONLY valid JSON."""


class PictureSuperiorityService:
    """Detects picture superiority effect — visual format distorting evidence weighting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        visual: str = "",
        textual: str = "",
        weighting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect picture superiority effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PICTURE_SUPERIORITY_PROMPT.format(
                situation=situation,
                visual=visual or "Not specified",
                textual=textual or "Not specified",
                weighting=weighting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PICTURE_SUPERIORITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "picture_superiority_present": data.get("picture_superiority_present", False),
            "severity": data.get("severity", ""),
            "visual_evidence": data.get("visual_evidence", ""),
            "textual_evidence": data.get("textual_evidence", ""),
            "format_bias": data.get("format_bias", ""),
            "actual_quality": data.get("actual_quality", ""),
            "vividness_effect": data.get("vividness_effect", ""),
            "recommendation": data.get("recommendation", ""),
        }
