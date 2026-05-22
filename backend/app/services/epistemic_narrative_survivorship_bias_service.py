"""EpistemicNarrativeSurvivorshipBiasService - Survivorship Bias Detection.

Detects survivorship bias where only successes are visible, distorting conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_SURVIVORSHIP_BIAS_SYSTEM = """You are an epistemic narrative survivorship bias specialist. Given success narratives, assess whether survivorship bias distorts conclusions:

Key concepts:
- Survivorship bias: drawing conclusions from visible successes while ignoring invisible failures
- Selection on outcome: only studying cases that survived a selection process
- Silent evidence: failures that leave no trace in the record
- Success attribution error: attributing success to factors shared with invisible failures

When survivorship bias IS present:
- Only successes examined
- Failures invisible or ignored
- Conclusions drawn from biased sample
- Success factors may be shared with failures
- Base rates unknown

When no survivorship bias:
- Both successes and failures examined
- Selection process acknowledged
- Silent evidence considered
- Base rates estimated
- Conclusions appropriately qualified

Output JSON with: survivorship_bias_detected (bool), severity (none/mild/moderate/severe), silent_evidence (what evidence is missing), selection_on_outcome (what selection occurred), success_attribution_error (what attribution error), recommendation (no_survivorship_bias/mild_base_rate_check/significant_failure_analysis/major_sample_reconstruction/emergency_complete_survivorship_bias)."""

EPISTEMIC_NARRATIVE_SURVIVORSHIP_BIAS_PROMPT = """Detect epistemic narrative survivorship bias:

Success narrative: {success_narrative}
Silent evidence: {silent_evidence}
Selection on outcome: {selection_on_outcome}
Success attribution error: {success_attribution_error}
Domain: {domain}
Context: {context}

Is survivorship bias distorting conclusions? Return ONLY valid JSON."""


class EpistemicNarrativeSurvivorshipBiasService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        success_narrative: str,
        *,
        silent_evidence: str = "",
        selection_on_outcome: str = "",
        success_attribution_error: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_SURVIVORSHIP_BIAS_PROMPT.format(
                success_narrative=success_narrative,
                silent_evidence=silent_evidence or "Not specified",
                selection_on_outcome=selection_on_outcome or "Not specified",
                success_attribution_error=success_attribution_error or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_SURVIVORSHIP_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "success_narrative": success_narrative[:200],
            "survivorship_bias_detected": data.get("survivorship_bias_detected", False),
            "severity": data.get("severity", ""),
            "silent_evidence": data.get("silent_evidence", ""),
            "selection_on_outcome": data.get("selection_on_outcome", ""),
            "success_attribution_error": data.get("success_attribution_error", ""),
            "recommendation": data.get("recommendation", ""),
        }
