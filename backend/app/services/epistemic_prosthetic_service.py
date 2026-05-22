"""EpistemicProstheticService — Epistemic Prosthetic Detection.

Detects need for epistemic prosthetic — artificial replacement for lost
intellectual function that cannot be naturally restored.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PROSTHETIC_SYSTEM = """You are an epistemic prosthetic specialist. Given permanent intellectual function loss, assess whether artificial replacement is needed:

Key concepts:
- Epistemic prosthetic: artificial replacement for lost intellectual function
- Amputation level: how much function was permanently lost
- Socket fit: how well prosthetic interfaces with remaining capacity
- Phantom sensation: feeling of function that no longer exists
- Myoelectric: prosthetic controlled by remaining intellectual signals
- Osseointegration: prosthetic directly connected to framework
- Functional vs cosmetic: working replacement vs appearance only

When epistemic prosthetic IS needed:
- Permanent intellectual function loss requiring replacement
- Significant function permanently lost
- Need for interface between prosthetic and remaining capacity
- Feeling of function that no longer exists
- Remaining signals available to control replacement
- Direct connection to framework possible
- Working replacement needed, not just appearance

When no prosthetic needed:
- No permanent function loss
- All function intact or recoverable
- No interface needed
- No phantom sensations
- Full natural control
- Complete framework
- Natural function sufficient

Output JSON with: prosthetic_needed (bool), severity (none/mild/moderate/severe), amputation_level (what permanent loss), socket_fit (what interface quality), phantom_sensation (what ghost function), functional_requirement (what working replacement), recommendation (no_prosthetic_needed/mild_augmentation/significant_prosthetic/major_replacement/comprehensive_intellectual_prosthetic_system)."""

EPISTEMIC_PROSTHETIC_PROMPT = """Detect epistemic prosthetic need:

Amputation level: {amputation_level}
Socket fit: {socket_fit}
Phantom sensation: {phantom_sensation}
Functional requirement: {functional_requirement}
Domain: {domain}
Context: {context}

Is artificial replacement needed for permanently lost intellectual function? Return ONLY valid JSON."""


class EpistemicProstheticService:
    """Detects epistemic prosthetic need — artificial intellectual function replacement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        amputation_level: str,
        *,
        socket_fit: str = "",
        phantom_sensation: str = "",
        functional_requirement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prosthetic need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PROSTHETIC_PROMPT.format(
                amputation_level=amputation_level,
                socket_fit=socket_fit or "Not specified",
                phantom_sensation=phantom_sensation or "Not specified",
                functional_requirement=functional_requirement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PROSTHETIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "amputation_level": amputation_level[:200],
            "prosthetic_needed": data.get("prosthetic_needed", False),
            "severity": data.get("severity", ""),
            "socket_fit": data.get("socket_fit", ""),
            "phantom_sensation": data.get("phantom_sensation", ""),
            "functional_requirement": data.get("functional_requirement", ""),
            "recommendation": data.get("recommendation", ""),
        }
