"""EpistemicTrustRepairFailureService — Epistemic Trust Repair Failure Detection.

Detects epistemic trust repair failure — inability to repair broken
intellectual trust after betrayal or disappointment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRUST_REPAIR_FAILURE_SYSTEM = """You are an epistemic trust repair failure specialist. Given inability to repair broken trust, assess trust repair failure:

Key concepts:
- Epistemic trust repair failure: inability to repair broken trust
- Permanent suspicion: unable to trust again after betrayal
- Repair attempts failing: efforts to rebuild trust not working
- Forgiveness block: unable to forgive intellectual betrayal
- Hypervigilance: constantly watching for new betrayal
- Generalization: one betrayal poisoning all trust
- Isolation spiral: broken trust leading to increasing isolation

When epistemic trust repair failure IS present:
- Inability to repair broken trust
- Unable to trust again
- Repair attempts failing
- Unable to forgive
- Constantly watching for betrayal
- One betrayal poisoning all
- Broken trust causing isolation

When no trust repair failure:
- Trust repairable
- Able to trust again
- Repair attempts succeeding
- Forgiveness possible
- Appropriate vigilance
- Betrayal contained
- Trust supporting connection

Output JSON with: trust_repair_failure_detected (bool), severity (none/mild/moderate/severe), permanent_suspicion (what unable to trust), repair_attempts_failing (what not working), forgiveness_block (what unable to forgive), isolation_spiral (what isolation from), recommendation (no_trust_repair_failure/mild_repair_support/significant_trust_rebuilding/major_intensive_forgiveness_work/emergency_complete_trust_collapse)."""

EPISTEMIC_TRUST_REPAIR_FAILURE_PROMPT = """Detect epistemic trust repair failure:

Permanent suspicion: {permanent_suspicion}
Repair attempts failing: {repair_attempts_failing}
Forgiveness block: {forgiveness_block}
Isolation spiral: {isolation_spiral}
Domain: {domain}
Context: {context}

Is there inability to repair broken intellectual trust? Return ONLY valid JSON."""


class EpistemicTrustRepairFailureService:
    """Detects epistemic trust repair failure — inability to repair broken trust."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        permanent_suspicion: str,
        *,
        repair_attempts_failing: str = "",
        forgiveness_block: str = "",
        isolation_spiral: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trust repair failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRUST_REPAIR_FAILURE_PROMPT.format(
                permanent_suspicion=permanent_suspicion,
                repair_attempts_failing=repair_attempts_failing or "Not specified",
                forgiveness_block=forgiveness_block or "Not specified",
                isolation_spiral=isolation_spiral or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRUST_REPAIR_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "permanent_suspicion": permanent_suspicion[:200],
            "trust_repair_failure_detected": data.get("trust_repair_failure_detected", False),
            "severity": data.get("severity", ""),
            "repair_attempts_failing": data.get("repair_attempts_failing", ""),
            "forgiveness_block": data.get("forgiveness_block", ""),
            "isolation_spiral": data.get("isolation_spiral", ""),
            "recommendation": data.get("recommendation", ""),
        }
