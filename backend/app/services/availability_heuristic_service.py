"""AvailabilityHeuristicService — Availability Bias Detection.

Identifies when judgments about frequency or probability are distorted
by how easily examples come to mind. Vivid, recent, or emotionally
charged events are overweighted; mundane but common events are ignored.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AVAILABILITY_SYSTEM = """You are an availability heuristic specialist. Given a probability or frequency judgment, assess whether it's distorted by availability:
- Are vivid/dramatic examples dominating the estimate?
- Are recent events being overweighted?
- Are emotionally charged cases distorting frequency estimates?
- Is media coverage creating a false sense of prevalence?
- What does the actual data say vs what "feels" right?

Output JSON with: availability_bias_present (bool), severity (none/mild/moderate/severe), availability_drivers (list of: driver_type (vivid/recent/emotional/media/personal_experience), specific_example, distortion_effect), estimated_frequency (what people think based on availability), actual_frequency (what data suggests), overestimation_factor (how much availability inflates the estimate), underestimated_alternatives (common things being ignored because they're not vivid), media_amplification (bool — is media coverage distorting perception?), recency_effect (bool — are recent events dominating?), personal_experience_effect (bool — is personal anecdote overriding statistics?), debiasing_approach (how to correct for availability), correct_reference_data (what data source would give accurate frequency), recommendation (judgment_valid/mild_correction_needed/major_correction_needed/seek_data)."""

AVAILABILITY_PROMPT = """Detect availability heuristic:

Judgment: {judgment}
Basis for judgment: {basis}
Domain: {domain}
Context: {context}

Is availability bias distorting this? Return ONLY valid JSON."""


class AvailabilityHeuristicService:
    """Detects availability heuristic distortions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect availability heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AVAILABILITY_PROMPT.format(
                judgment=judgment,
                basis=basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AVAILABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "availability_bias_present": data.get("availability_bias_present", False),
            "severity": data.get("severity", ""),
            "availability_drivers": data.get("availability_drivers", []),
            "estimated_frequency": data.get("estimated_frequency", ""),
            "actual_frequency": data.get("actual_frequency", ""),
            "overestimation_factor": data.get("overestimation_factor", ""),
            "underestimated_alternatives": data.get("underestimated_alternatives", []),
            "media_amplification": data.get("media_amplification", False),
            "recency_effect": data.get("recency_effect", False),
            "personal_experience_effect": data.get("personal_experience_effect", False),
            "debiasing_approach": data.get("debiasing_approach", ""),
            "correct_reference_data": data.get("correct_reference_data", ""),
            "recommendation": data.get("recommendation", ""),
        }
