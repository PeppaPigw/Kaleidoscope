"""EpistemicTransplantRejectionService — Epistemic Transplant Rejection Detection.

Detects epistemic transplant rejection — intellectual systems rejecting
newly introduced components as foreign bodies.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRANSPLANT_REJECTION_SYSTEM = """You are an epistemic transplant rejection specialist. Given newly introduced intellectual components, assess rejection:

Key concepts:
- Epistemic transplant rejection: system attacking new components
- Hyperacute: immediate violent rejection
- Acute: early rejection within days
- Chronic: slow ongoing rejection over time
- Immunosuppression: dampening rejection response
- Graft-versus-host: new component attacking recipient
- Tolerance induction: teaching acceptance of new component

When epistemic transplant rejection IS occurring:
- System attacking newly introduced components
- Immediate violent rejection response
- Early rejection signs appearing
- Slow ongoing rejection present
- Insufficient dampening of rejection
- New component attacking recipient system
- Failed acceptance teaching

When no transplant rejection:
- New components accepted
- No attack response
- No rejection signs
- Stable integration
- Natural tolerance present
- Harmonious coexistence
- Successful acceptance

Output JSON with: rejection_detected (bool), severity (none/mild/moderate/severe), rejection_type (what category), immune_response (what attack pattern), graft_status (what component state), immunosuppression_need (what dampening required), recommendation (no_rejection_detected/mild_monitoring/significant_immunosuppression/major_rescue_therapy/emergency_graft_failure)."""

EPISTEMIC_TRANSPLANT_REJECTION_PROMPT = """Detect epistemic transplant rejection:

Rejection type: {rejection_type}
Immune response: {immune_response}
Graft status: {graft_status}
Immunosuppression need: {immunosuppression_need}
Domain: {domain}
Context: {context}

Is the intellectual system rejecting newly introduced components? Return ONLY valid JSON."""


class EpistemicTransplantRejectionService:
    """Detects epistemic transplant rejection — systems attacking new components."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rejection_type: str,
        *,
        immune_response: str = "",
        graft_status: str = "",
        immunosuppression_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic transplant rejection."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRANSPLANT_REJECTION_PROMPT.format(
                rejection_type=rejection_type,
                immune_response=immune_response or "Not specified",
                graft_status=graft_status or "Not specified",
                immunosuppression_need=immunosuppression_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRANSPLANT_REJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rejection_type": rejection_type[:200],
            "rejection_detected": data.get("rejection_detected", False),
            "severity": data.get("severity", ""),
            "immune_response": data.get("immune_response", ""),
            "graft_status": data.get("graft_status", ""),
            "immunosuppression_need": data.get("immunosuppression_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
