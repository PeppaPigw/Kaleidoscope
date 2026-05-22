"""ContrastEffectService — Contrast Effect Detection.

Detects contrast effect — judging something as better or worse
than it actually is because of what it's compared to. A mediocre
option looks great next to a terrible one. An average candidate
looks weak after an exceptional one. Relative comparison
distorts absolute judgment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONTRAST_SYSTEM = """You are a contrast effect specialist. Given a judgment, assess whether the evaluation is distorted by what it's being compared to rather than reflecting absolute quality:

Key concepts:
- Contrast effect: judgment shifted by comparison context
- Sequential contrast: previous item affects evaluation of next
- Simultaneous contrast: adjacent options distort each other
- Assimilation vs. contrast: sometimes context pulls toward, sometimes pushes away
- Reference point manipulation: strategic use of comparisons
- Perceptual contrast: physical stimuli (warm water feels hot after cold)
- Social contrast: people seem better/worse depending on who they're near

When contrast effect IS present:
- An average option rated highly because alternatives are terrible
- A good option rated poorly because it follows an exceptional one
- Salary seems generous only because the previous offer was low
- A product seems cheap only because it's next to an expensive one
- Interview candidate rated based on who came before, not absolute merit
- Strategic placement of a bad option to make another look better

When the comparison IS appropriate:
- Relative comparison is genuinely the right evaluation method
- The comparison context is the actual decision context
- Absolute quality is less relevant than relative positioning
- The comparison reveals genuine differences that matter
- The evaluator is aware of and correcting for contrast effects

Output JSON with: contrast_effect_present (bool), severity (none/mild/moderate/severe), judgment (what is being evaluated), comparison_context (what is it being compared to), absolute_quality (what is the absolute quality?), relative_quality (what is the relative quality?), context_manipulation (bool — is the comparison context strategically chosen?), sequential_effect (bool — is order affecting judgment?), distortion_direction (is the judgment inflated or deflated?), appropriate_comparison (what would be a fair comparison?), recommendation (comparison_appropriate/mild_contrast/significant_distortion/major_context_manipulation/evaluate_absolutely)."""

CONTRAST_PROMPT = """Detect contrast effect:

Judgment: {judgment}
Comparison: {comparison}
Context: {eval_context}
Sequence: {sequence}
Domain: {domain}
Additional context: {context}

Is the evaluation distorted by what it's being compared to? Return ONLY valid JSON."""


class ContrastEffectService:
    """Detects contrast effect — judgment distorted by comparison context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        comparison: str = "",
        eval_context: str = "",
        sequence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect contrast effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTRAST_PROMPT.format(
                judgment=judgment,
                comparison=comparison or "Not specified",
                eval_context=eval_context or "Not specified",
                sequence=sequence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONTRAST_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "contrast_effect_present": data.get("contrast_effect_present", False),
            "severity": data.get("severity", ""),
            "comparison_context": data.get("comparison_context", ""),
            "absolute_quality": data.get("absolute_quality", ""),
            "relative_quality": data.get("relative_quality", ""),
            "context_manipulation": data.get("context_manipulation", False),
            "sequential_effect": data.get("sequential_effect", False),
            "distortion_direction": data.get("distortion_direction", ""),
            "appropriate_comparison": data.get("appropriate_comparison", ""),
            "recommendation": data.get("recommendation", ""),
        }
