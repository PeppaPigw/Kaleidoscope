"""ReversibilityNeglectService — Reversibility Neglect Detection.

Detects reversibility neglect — the failure to consider whether a
decision can be undone. Irreversible decisions deserve more
deliberation, while reversible ones can be made faster. Neglecting
this distinction leads to either reckless irreversible choices or
paralysis on easily-reversed ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REVERSIBILITY_NEGLECT_SYSTEM = """You are a reversibility neglect specialist. Given a decision, assess whether reversibility has been adequately considered:

Key concepts:
- Reversibility: can the decision be undone or modified later?
- One-way doors: irreversible decisions that deserve careful deliberation
- Two-way doors: reversible decisions that can be made quickly
- Path dependence: how current choices constrain future options
- Option value: the value of keeping future choices open
- Commitment escalation: small irreversible steps leading to lock-in
- Regret minimization: irreversible decisions have higher regret potential

When reversibility neglect IS present:
- Irreversible decision made with insufficient deliberation
- No consideration of whether the choice can be undone
- Treating a one-way door as a two-way door
- Treating a two-way door as a one-way door (analysis paralysis)
- Ignoring path dependence and lock-in effects
- Not building in reversibility where possible
- Failing to distinguish between reversible and irreversible components

When reversibility neglect is NOT present:
- Reversibility explicitly assessed for the decision
- One-way doors get proportionally more deliberation
- Two-way doors are decided quickly without over-analysis
- Path dependence and lock-in are considered
- Reversibility is built in where possible (pilots, trials, stages)
- Irreversible components are identified and given extra scrutiny
- Decision speed is calibrated to reversibility

Output JSON with: neglect_present (bool), severity (none/mild/moderate/severe), reversibility (fully_reversible/partially_reversible/mostly_irreversible/fully_irreversible), deliberation_match (appropriate/under_deliberated/over_deliberated), lock_in_risks (what gets locked in), mitigation (how to add reversibility), recommendation (no_neglect/calibrate_deliberation/add_reversibility/high_risk_irreversible/treat_as_two_way_door)."""

REVERSIBILITY_NEGLECT_PROMPT = """Detect reversibility neglect:

Decision: {decision}
Reversibility: {reversibility}
Deliberation level: {deliberation}
Stakes: {stakes}
Domain: {domain}
Context: {context}

Has reversibility been adequately considered in this decision? Return ONLY valid JSON."""


class ReversibilityNeglectService:
    """Detects reversibility neglect — failure to consider if decisions can be undone."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        reversibility: str = "",
        deliberation: str = "",
        stakes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reversibility neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REVERSIBILITY_NEGLECT_PROMPT.format(
                decision=decision,
                reversibility=reversibility or "Not specified",
                deliberation=deliberation or "Not specified",
                stakes=stakes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REVERSIBILITY_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "neglect_present": data.get("neglect_present", False),
            "severity": data.get("severity", ""),
            "reversibility": data.get("reversibility", ""),
            "deliberation_match": data.get("deliberation_match", ""),
            "lock_in_risks": data.get("lock_in_risks", ""),
            "mitigation": data.get("mitigation", ""),
            "recommendation": data.get("recommendation", ""),
        }
