"""EpistemicInfantilizationService — Epistemic Infantilization Detection.

Detects epistemic infantilization — treating capable agents as
epistemically incapable, denying their ability to handle information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFANTILIZATION_SYSTEM = """You are an epistemic infantilization specialist. Given a knowledge-sharing interaction, assess whether capable agents are being treated as epistemically incapable:

Key concepts:
- Epistemic infantilization: treating capable agents as incapable
- Capability denial: denying others' epistemic capabilities
- Oversimplification for protection: oversimplifying to protect
- Condescending withholding: withholding information condescendingly
- Competence underestimation: underestimating others' competence
- Protective dumbing down: dumbing down for supposed protection
- Agency denial: denying others' epistemic agency

When epistemic infantilization IS present:
- Capable agents treated as epistemically incapable
- Others' epistemic capabilities denied
- Information oversimplified beyond what's needed
- Information withheld condescendingly
- Competence systematically underestimated
- Content dumbed down for supposed protection
- Epistemic agency denied to capable agents

When appropriate adaptation is present:
- Communication adapted to genuine needs
- Capabilities accurately assessed
- Simplification proportionate to audience
- Information shared at appropriate level
- Competence accurately estimated
- Content adapted not dumbed down
- Agency respected and supported

Output JSON with: infantilization_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), capability_denied (what capability is denied), actual_capability (what capability actually exists), mechanism (how infantilization works), recommendation (appropriate_adaptation/mild_underestimation/significant_epistemic_infantilization/major_agency_denial/respect_epistemic_capability)."""

EPISTEMIC_INFANTILIZATION_PROMPT = """Detect epistemic infantilization:

Interaction: {interaction}
Capability denied: {denied}
Actual capability: {actual}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Are capable agents being treated as epistemically incapable? Return ONLY valid JSON."""


class EpistemicInfantilizationService:
    """Detects epistemic infantilization — treating capable agents as incapable."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        denied: str = "",
        actual: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic infantilization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFANTILIZATION_PROMPT.format(
                interaction=interaction,
                denied=denied or "Not specified",
                actual=actual or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFANTILIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "infantilization_present": data.get("infantilization_present", False),
            "severity": data.get("severity", ""),
            "capability_denied": data.get("capability_denied", ""),
            "actual_capability": data.get("actual_capability", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
