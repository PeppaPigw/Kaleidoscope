"""EpistemicMethodologyStreetlightEffectService - Epistemic Methodology Streetlight Effect Detection.

Detects streetlight effect searching where it's easy rather than where answers are.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METHODOLOGY_STREETLIGHT_EFFECT_SYSTEM = """You are an epistemic methodology streetlight effect specialist. Given convenience over relevance, assess search misdirection:

Key concepts:
- Epistemic methodology streetlight effect: searching where it is easy rather than where answers are
- Convenience over relevance: prioritizing accessible evidence over relevant evidence
- Measurability bias: treating measurable variables as the important ones
- Tool determines question: available methods shape the question asked
- Accessibility distortion: accessible data distorts inquiry

When streetlight effect IS present:
- Convenience overrides relevance
- Measurable factors are overvalued
- Tools determine the research question
- Accessible data distorts the analysis
- Hard-to-measure answers are neglected

When no streetlight effect:
- Relevance guides search
- Measurability limits are acknowledged
- Tools serve the question
- Accessibility bias is checked
- Hard-to-measure evidence is considered

Output JSON with: streetlight_effect_detected (bool), severity (none/mild/moderate/severe), measurability_bias (what measurability bias appears), tool_determines_question (how tool shapes question), accessibility_distortion (what accessibility distorts), recommendation (no_streetlight_effect/mild_relevance_check/significant_search_redesign/major_method_reassessment/emergency_complete_streetlight_effect)."""

EPISTEMIC_METHODOLOGY_STREETLIGHT_EFFECT_PROMPT = """Detect epistemic methodology streetlight effect:

Convenience over relevance: {convenience_over_relevance}
Measurability bias: {measurability_bias}
Tool determines question: {tool_determines_question}
Accessibility distortion: {accessibility_distortion}
Domain: {domain}
Context: {context}

Is the search happening where it is easy rather than where answers are? Return ONLY valid JSON."""


class EpistemicMethodologyStreetlightEffectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        convenience_over_relevance: str,
        *,
        measurability_bias: str = "",
        tool_determines_question: str = "",
        accessibility_distortion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METHODOLOGY_STREETLIGHT_EFFECT_PROMPT.format(
                convenience_over_relevance=convenience_over_relevance,
                measurability_bias=measurability_bias or "Not specified",
                tool_determines_question=tool_determines_question or "Not specified",
                accessibility_distortion=accessibility_distortion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METHODOLOGY_STREETLIGHT_EFFECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "convenience_over_relevance": convenience_over_relevance[:200],
            "streetlight_effect_detected": data.get("streetlight_effect_detected", False),
            "severity": data.get("severity", ""),
            "measurability_bias": data.get("measurability_bias", ""),
            "tool_determines_question": data.get("tool_determines_question", ""),
            "accessibility_distortion": data.get("accessibility_distortion", ""),
            "recommendation": data.get("recommendation", ""),
        }
