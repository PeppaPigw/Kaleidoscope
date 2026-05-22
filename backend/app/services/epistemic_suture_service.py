"""EpistemicSutureService — Epistemic Suture Detection.

Detects need for epistemic suturing — closing intellectual wounds
to promote healing and prevent infection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUTURE_SYSTEM = """You are an epistemic suture specialist. Given intellectual wounds, assess suturing need:

Key concepts:
- Epistemic suture: closing intellectual wounds
- Primary closure: immediate wound closing
- Secondary intention: allowing wound to heal open
- Delayed primary: closing after initial observation
- Wound tension: forces pulling edges apart
- Dehiscence: wound reopening after closure
- Approximation: bringing wound edges together

When epistemic suturing IS needed:
- Open intellectual wound present
- Immediate closure beneficial
- Wound edges can be approximated
- Tension manageable
- Low infection risk with closure
- Healing promoted by closing
- Dehiscence risk acceptable

When no suturing needed:
- No open wound
- Wound too contaminated to close
- Edges cannot be approximated
- Excessive tension
- High infection risk
- Better healing open
- Self-closing naturally

Output JSON with: suture_needed (bool), severity (none/mild/moderate/severe), wound_type (what injury), closure_method (what technique), tension_status (what forces), dehiscence_risk (what reopening risk), recommendation (no_suture_needed/mild_adhesive/significant_simple_suture/major_layered_closure/emergency_damage_control_closure)."""

EPISTEMIC_SUTURE_PROMPT = """Detect epistemic suturing need:

Wound type: {wound_type}
Closure method: {closure_method}
Tension status: {tension_status}
Dehiscence risk: {dehiscence_risk}
Domain: {domain}
Context: {context}

Is there an open intellectual wound that needs closing? Return ONLY valid JSON."""


class EpistemicSutureService:
    """Detects epistemic suturing need — closing intellectual wounds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        wound_type: str,
        *,
        closure_method: str = "",
        tension_status: str = "",
        dehiscence_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic suturing need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUTURE_PROMPT.format(
                wound_type=wound_type,
                closure_method=closure_method or "Not specified",
                tension_status=tension_status or "Not specified",
                dehiscence_risk=dehiscence_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "wound_type": wound_type[:200],
            "suture_needed": data.get("suture_needed", False),
            "severity": data.get("severity", ""),
            "closure_method": data.get("closure_method", ""),
            "tension_status": data.get("tension_status", ""),
            "dehiscence_risk": data.get("dehiscence_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
