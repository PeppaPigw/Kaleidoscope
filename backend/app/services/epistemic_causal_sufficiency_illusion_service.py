"""EpistemicCausalSufficiencyIllusionService — Epistemic Causal Sufficiency Illusion Detection.

Detects epistemic causal sufficiency illusion — believing one cause is
sufficient when multiple causes are needed for the effect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_SUFFICIENCY_ILLUSION_SYSTEM = """You are an epistemic causal sufficiency illusion specialist. Given belief that one cause suffices when multiple are needed, assess sufficiency illusion:

Key concepts:
- Epistemic causal sufficiency illusion: believing one cause sufficient when multiple needed
- Single-factor thinking: thinking one factor explains everything
- Necessary-sufficient confusion: confusing necessary with sufficient conditions
- Overdetermination blindness: blind to overdetermination
- Threshold ignorance: ignoring that effects require threshold of causes
- Interaction necessity: missing that causes must interact to produce effect
- Enabling condition neglect: neglecting enabling conditions

When epistemic causal sufficiency illusion IS present:
- One cause believed sufficient
- Single factor thinking
- Necessary confused with sufficient
- Overdetermination missed
- Thresholds ignored
- Interactions missed
- Enabling conditions neglected

When no sufficiency illusion:
- Multiple causes recognized as needed
- Multi-factor thinking
- Necessary and sufficient distinguished
- Overdetermination considered
- Thresholds recognized
- Interactions considered
- Enabling conditions included

Output JSON with: causal_sufficiency_illusion_detected (bool), severity (none/mild/moderate/severe), single_factor_thinking (what single factor), necessary_sufficient_confusion (what confused), threshold_ignorance (what thresholds ignored), enabling_condition_neglect (what conditions neglected), recommendation (no_sufficiency_illusion/mild_multicausal_awareness/significant_sufficiency_analysis/major_intensive_causal_completeness/emergency_complete_sufficiency_illusion)."""

EPISTEMIC_CAUSAL_SUFFICIENCY_ILLUSION_PROMPT = """Detect epistemic causal sufficiency illusion:

Single factor thinking: {single_factor_thinking}
Necessary-sufficient confusion: {necessary_sufficient_confusion}
Threshold ignorance: {threshold_ignorance}
Enabling condition neglect: {enabling_condition_neglect}
Domain: {domain}
Context: {context}

Is one cause believed sufficient when multiple are needed? Return ONLY valid JSON."""


class EpistemicCausalSufficiencyIllusionService:
    """Detects epistemic causal sufficiency illusion — one cause not enough."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        single_factor_thinking: str,
        *,
        necessary_sufficient_confusion: str = "",
        threshold_ignorance: str = "",
        enabling_condition_neglect: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic causal sufficiency illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_SUFFICIENCY_ILLUSION_PROMPT.format(
                single_factor_thinking=single_factor_thinking,
                necessary_sufficient_confusion=necessary_sufficient_confusion or "Not specified",
                threshold_ignorance=threshold_ignorance or "Not specified",
                enabling_condition_neglect=enabling_condition_neglect or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_SUFFICIENCY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "single_factor_thinking": single_factor_thinking[:200],
            "causal_sufficiency_illusion_detected": data.get("causal_sufficiency_illusion_detected", False),
            "severity": data.get("severity", ""),
            "necessary_sufficient_confusion": data.get("necessary_sufficient_confusion", ""),
            "threshold_ignorance": data.get("threshold_ignorance", ""),
            "enabling_condition_neglect": data.get("enabling_condition_neglect", ""),
            "recommendation": data.get("recommendation", ""),
        }
