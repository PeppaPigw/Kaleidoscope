"""EpistemicValidationAddictionService — Epistemic Validation Addiction Detection.

Detects epistemic validation addiction — addictive dependence on intellectual
approval from others to feel one's thinking has value.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VALIDATION_ADDICTION_SYSTEM = """You are an epistemic validation addiction specialist. Given addictive dependence on approval, assess addiction:

Key concepts:
- Epistemic validation addiction: dependent on others' approval
- External locus: value only from others' judgment
- Approval seeking: constantly seeking intellectual validation
- Withdrawal: collapse without regular validation
- Tolerance: needing more validation over time
- Self-worth fusion: intellectual worth equals approval received
- People pleasing: shaping thinking to get approval

When epistemic validation addiction IS present:
- Dependent on others' approval
- Value only from judgment
- Constantly seeking validation
- Collapse without validation
- Needing more over time
- Worth equals approval
- Shaping thinking for approval

When no validation addiction:
- Self-validated thinking
- Internal value sense
- Sharing without needing approval
- Stable without validation
- Consistent need level
- Worth independent of approval
- Authentic thinking

Output JSON with: validation_addiction_detected (bool), severity (none/mild/moderate/severe), external_locus (what depending on), approval_seeking (what seeking), withdrawal_pattern (what collapse), people_pleasing (what shaping), recommendation (no_validation_addiction/mild_self_validation_practice/significant_locus_shift/major_intensive_addiction_work/emergency_severe_dependence)."""

EPISTEMIC_VALIDATION_ADDICTION_PROMPT = """Detect epistemic validation addiction:

External locus: {external_locus}
Approval seeking: {approval_seeking}
Withdrawal pattern: {withdrawal_pattern}
People pleasing: {people_pleasing}
Domain: {domain}
Context: {context}

Is there addictive dependence on intellectual approval from others? Return ONLY valid JSON."""


class EpistemicValidationAddictionService:
    """Detects epistemic validation addiction — dependent on intellectual approval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        external_locus: str,
        *,
        approval_seeking: str = "",
        withdrawal_pattern: str = "",
        people_pleasing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic validation addiction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VALIDATION_ADDICTION_PROMPT.format(
                external_locus=external_locus,
                approval_seeking=approval_seeking or "Not specified",
                withdrawal_pattern=withdrawal_pattern or "Not specified",
                people_pleasing=people_pleasing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VALIDATION_ADDICTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "external_locus": external_locus[:200],
            "validation_addiction_detected": data.get("validation_addiction_detected", False),
            "severity": data.get("severity", ""),
            "approval_seeking": data.get("approval_seeking", ""),
            "withdrawal_pattern": data.get("withdrawal_pattern", ""),
            "people_pleasing": data.get("people_pleasing", ""),
            "recommendation": data.get("recommendation", ""),
        }
