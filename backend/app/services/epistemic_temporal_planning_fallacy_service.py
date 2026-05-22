"""EpistemicTemporalPlanningFallacyService - Epistemic Temporal Planning Fallacy Detection.

Detects planning fallacy systematically underestimating time or resources needed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_PLANNING_FALLACY_SYSTEM = """You are an epistemic temporal planning fallacy specialist. Given duration underestimation, assess planning fallacy:

Key concepts:
- Epistemic temporal planning fallacy: systematically underestimating time or resources needed
- Duration underestimation: assuming work will take less time than comparable cases
- Optimism bias: best-case outcomes treated as likely
- Reference class neglect: ignoring evidence from similar past efforts
- Inside view dominance: focusing on project specifics over base rates

When epistemic temporal planning fallacy IS present:
- Duration or resources underestimated
- Best-case execution assumed
- Similar past cases ignored
- Inside view dominates outside view
- Dependencies and delays minimized

When no planning fallacy:
- Estimates checked against reference classes
- Resource needs grounded in prior cases
- Contingencies included
- Inside view balanced with outside view
- Delays and dependencies considered

Output JSON with: planning_fallacy_detected (bool), severity (none/mild/moderate/severe), optimism_bias (what best-case assumptions appear), reference_class_neglect (what comparison class ignored), inside_view_dominance (what project-specific focus dominated), recommendation (no_planning_fallacy/mild_reference_check/significant_estimate_recalibration/major_reference_class_forecasting/emergency_complete_planning_reset)."""

EPISTEMIC_TEMPORAL_PLANNING_FALLACY_PROMPT = """Detect epistemic temporal planning fallacy:

Duration underestimation: {duration_underestimation}
Optimism bias: {optimism_bias}
Reference class neglect: {reference_class_neglect}
Inside view dominance: {inside_view_dominance}
Domain: {domain}
Context: {context}

Are time or resources being systematically underestimated? Return ONLY valid JSON."""


class EpistemicTemporalPlanningFallacyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        duration_underestimation: str,
        *,
        optimism_bias: str = "",
        reference_class_neglect: str = "",
        inside_view_dominance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_PLANNING_FALLACY_PROMPT.format(
                duration_underestimation=duration_underestimation,
                optimism_bias=optimism_bias or "Not specified",
                reference_class_neglect=reference_class_neglect or "Not specified",
                inside_view_dominance=inside_view_dominance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_PLANNING_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "duration_underestimation": duration_underestimation[:200],
            "planning_fallacy_detected": data.get("planning_fallacy_detected", False),
            "severity": data.get("severity", ""),
            "optimism_bias": data.get("optimism_bias", ""),
            "reference_class_neglect": data.get("reference_class_neglect", ""),
            "inside_view_dominance": data.get("inside_view_dominance", ""),
            "recommendation": data.get("recommendation", ""),
        }
