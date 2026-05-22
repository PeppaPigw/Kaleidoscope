"""OmissionCommissionService — Omission-Commission Asymmetry Detection.

Detects omission-commission asymmetry — treating harmful actions as
morally worse than equally harmful inactions, or vice versa, when
the outcomes are equivalent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OMISSION_COMMISSION_SYSTEM = """You are an omission-commission asymmetry specialist. Given a moral judgment, assess whether actions and inactions with equal outcomes are being treated differently:

Key concepts:
- Omission-commission asymmetry: treating acts worse than omissions
- Act-omission distinction: moral difference between doing and allowing
- Trolley problem logic: active harm vs. passive allowing
- Moral responsibility asymmetry: more blame for acts than omissions
- Causal contribution: acts seen as more causal than omissions
- Intention attribution: acts assumed more intentional
- Outcome equivalence: same outcome judged differently by path

When omission-commission asymmetry IS present:
- Same outcome judged differently based on act vs. omission
- Harmful action condemned while equally harmful inaction excused
- Moral responsibility assigned asymmetrically for equal outcomes
- Causal contribution overweighted for acts vs. omissions
- Intention assumed for acts but not omissions
- Outcome equivalence ignored in moral judgment
- Bias toward judging commission more harshly

When distinction is appropriate:
- Genuine moral difference between act and omission in context
- Causal contribution genuinely different
- Intention genuinely different
- Responsibility genuinely asymmetric
- Context makes distinction morally relevant
- Outcomes not actually equivalent
- Duty to act vs. duty not to harm genuinely different

Output JSON with: asymmetry_present (bool), severity (none/mild/moderate/severe), judgment (what moral judgment is made), action (what action is judged), omission (what omission is compared), outcome_equivalence (whether outcomes are equivalent), recommendation (appropriate_distinction/mild_asymmetry/significant_omission_commission_bias/major_outcome_blindness/judge_by_outcomes)."""

OMISSION_COMMISSION_PROMPT = """Detect omission-commission asymmetry:

Judgment: {judgment}
Action evaluated: {action}
Omission compared: {omission}
Outcomes: {outcomes}
Domain: {domain}
Context: {context}

Are actions and inactions with equivalent outcomes being judged differently? Return ONLY valid JSON."""


class OmissionCommissionService:
    """Detects omission-commission asymmetry — acts judged differently from omissions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        action: str = "",
        omission: str = "",
        outcomes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect omission-commission asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OMISSION_COMMISSION_PROMPT.format(
                judgment=judgment,
                action=action or "Not specified",
                omission=omission or "Not specified",
                outcomes=outcomes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OMISSION_COMMISSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "asymmetry_present": data.get("asymmetry_present", False),
            "severity": data.get("severity", ""),
            "action": data.get("action", ""),
            "omission": data.get("omission", ""),
            "outcome_equivalence": data.get("outcome_equivalence", ""),
            "recommendation": data.get("recommendation", ""),
        }
