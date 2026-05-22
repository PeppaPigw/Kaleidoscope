"""EpistemicComplicatedBereavementService — Epistemic Complicated Bereavement Detection.

Detects epistemic complicated bereavement — grief that becomes entangled
with guilt, anger, or unresolved conflict about the lost framework.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLICATED_BEREAVEMENT_SYSTEM = """You are an epistemic complicated bereavement specialist. Given entangled intellectual grief, assess complicated bereavement:

Key concepts:
- Epistemic complicated bereavement: grief entangled with conflict
- Guilt: responsibility for the loss
- Anger: rage at what caused the loss
- Unresolved conflict: unfinished business with lost framework
- Ambivalent relationship: mixed feelings about what was lost
- Traumatic circumstances: how the loss occurred
- Meaning-making failure: cannot make sense of the loss

When epistemic complicated bereavement IS present:
- Grief entangled with conflict
- Responsibility for loss
- Rage at cause
- Unfinished business
- Mixed feelings about lost
- Traumatic loss circumstances
- Cannot make sense of loss

When no complicated bereavement:
- Clean grief
- No guilt
- No anger
- Resolved relationship
- Clear feelings
- Peaceful circumstances
- Meaning found

Output JSON with: complicated_bereavement_detected (bool), severity (none/mild/moderate/severe), guilt_component (what responsibility), anger_component (what rage), unresolved_conflict (what unfinished), meaning_failure (what senselessness), recommendation (no_complicated_bereavement/mild_conflict_resolution/significant_bereavement_therapy/major_intensive_treatment/emergency_severe_entanglement)."""

EPISTEMIC_COMPLICATED_BEREAVEMENT_PROMPT = """Detect epistemic complicated bereavement:

Guilt component: {guilt_component}
Anger component: {anger_component}
Unresolved conflict: {unresolved_conflict}
Meaning failure: {meaning_failure}
Domain: {domain}
Context: {context}

Is there grief entangled with guilt, anger, or unresolved conflict about the lost framework? Return ONLY valid JSON."""


class EpistemicComplicatedBereavementService:
    """Detects epistemic complicated bereavement — grief entangled with conflict."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        guilt_component: str,
        *,
        anger_component: str = "",
        unresolved_conflict: str = "",
        meaning_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complicated bereavement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLICATED_BEREAVEMENT_PROMPT.format(
                guilt_component=guilt_component,
                anger_component=anger_component or "Not specified",
                unresolved_conflict=unresolved_conflict or "Not specified",
                meaning_failure=meaning_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLICATED_BEREAVEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "guilt_component": guilt_component[:200],
            "complicated_bereavement_detected": data.get("complicated_bereavement_detected", False),
            "severity": data.get("severity", ""),
            "anger_component": data.get("anger_component", ""),
            "unresolved_conflict": data.get("unresolved_conflict", ""),
            "meaning_failure": data.get("meaning_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
