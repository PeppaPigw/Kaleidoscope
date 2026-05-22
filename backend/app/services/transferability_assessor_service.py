"""TransferabilityAssessorService — Cross-Context Validity Assessment.

Evaluates whether research findings transfer across contexts: different
populations, settings, scales, time periods, or domains. Identifies
boundary conditions and moderating factors that affect generalizability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRANSFER_SYSTEM = """You are a transferability assessment specialist. Given a finding and a target context, evaluate whether the finding will hold in the new context. Consider:
- Population differences: does the finding depend on specific demographics?
- Setting differences: lab vs field, controlled vs natural, scale differences
- Temporal differences: has the world changed since the finding was established?
- Mechanism preservation: does the causal mechanism still operate in the new context?
- Moderating factors: what variables might strengthen or weaken the effect?
- Boundary conditions: where exactly does the finding stop applying?

Output JSON with: transfer_assessment.transferability_score (0-1), transfer_assessment.verdict (highly_transferable/likely_transferable/uncertain/unlikely/non_transferable), transfer_assessment.mechanism_preserved (bool, does the causal mechanism still apply), transfer_assessment.key_differences (list of: difference, impact_on_transfer, severity), transfer_assessment.moderating_factors (list of: factor, direction, magnitude), transfer_assessment.boundary_conditions (list of conditions where transfer breaks down), transfer_assessment.adaptations_needed (what modifications would make it transfer), transfer_assessment.confidence (0-1), transfer_assessment.recommendation (apply_directly/adapt_then_apply/test_first/do_not_transfer)."""

TRANSFER_PROMPT = """Assess transferability of this finding to a new context:

Finding: {finding}
Original context: {original_context}
Target context: {target_context}
Domain: {domain}

Will this finding hold in the new context? Return ONLY valid JSON."""


class TransferabilityAssessorService:
    """Evaluates whether findings transfer across contexts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess_transfer(
        self,
        finding: str,
        target_context: str,
        *,
        original_context: str = "",
        domain: str = "",
    ) -> dict:
        """Assess whether a finding transfers to a new context."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRANSFER_PROMPT.format(
                finding=finding,
                original_context=original_context or "Original research context",
                target_context=target_context,
                domain=domain or "research",
            ),
            system=TRANSFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        assessment = data.get("transfer_assessment", data)

        return {
            "finding": finding[:200],
            "target_context": target_context[:200],
            "transferability_score": assessment.get("transferability_score", 0),
            "verdict": assessment.get("verdict", ""),
            "mechanism_preserved": assessment.get("mechanism_preserved", None),
            "key_differences": assessment.get("key_differences", []),
            "moderating_factors": assessment.get("moderating_factors", []),
            "boundary_conditions": assessment.get("boundary_conditions", []),
            "adaptations_needed": assessment.get("adaptations_needed", []),
            "confidence": assessment.get("confidence", 0),
            "recommendation": assessment.get("recommendation", ""),
        }
