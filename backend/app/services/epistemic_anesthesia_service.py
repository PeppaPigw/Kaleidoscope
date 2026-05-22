"""EpistemicAnesthesiaService — Epistemic Anesthesia Detection.

Detects epistemic anesthesia — numbing of intellectual sensitivity
preventing detection of important signals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANESTHESIA_SYSTEM = """You are an epistemic anesthesia specialist. Given a sensitivity pattern, assess whether intellectual sensitivity has been numbed:

Key concepts:
- Epistemic anesthesia: numbing of intellectual sensitivity
- Signal blindness: inability to detect important signals
- Sensitivity loss: loss of sensitivity to important distinctions
- Desensitization: becoming desensitized to important information
- Numbness: intellectual numbness to relevant stimuli
- Detection failure: failure to detect what should be noticed
- Awareness suppression: awareness suppressed or dulled

When epistemic anesthesia IS present:
- Intellectual sensitivity numbed
- Inability to detect important signals
- Loss of sensitivity to important distinctions
- Desensitized to important information
- Intellectual numbness to relevant stimuli
- Failure to detect what should be noticed
- Awareness suppressed or dulled

When appropriate sensitivity is present:
- Intellectual sensitivity calibrated
- Important signals detected reliably
- Sensitivity to important distinctions maintained
- Appropriately responsive to important information
- Alert to relevant stimuli
- Detecting what needs to be noticed
- Awareness active and calibrated

Output JSON with: anesthesia_present (bool), severity (none/mild/moderate/severe), system (what system is numbed), sensitivity_loss (what sensitivity is lost), signals_missed (what signals are missed), cause (what causes the numbing), recommendation (appropriate_sensitivity/mild_desensitization/significant_anesthesia/major_numbness/restore_sensitivity)."""

EPISTEMIC_ANESTHESIA_PROMPT = """Detect epistemic anesthesia:

System: {system}
Sensitivity loss: {sensitivity_loss}
Signals missed: {signals_missed}
Cause: {cause}
Domain: {domain}
Context: {context}

Has intellectual sensitivity been numbed preventing detection of important signals? Return ONLY valid JSON."""


class EpistemicAnesthesiaService:
    """Detects epistemic anesthesia — numbing of intellectual sensitivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        sensitivity_loss: str = "",
        signals_missed: str = "",
        cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic anesthesia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANESTHESIA_PROMPT.format(
                system=system,
                sensitivity_loss=sensitivity_loss or "Not specified",
                signals_missed=signals_missed or "Not specified",
                cause=cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANESTHESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "anesthesia_present": data.get("anesthesia_present", False),
            "severity": data.get("severity", ""),
            "sensitivity_loss": data.get("sensitivity_loss", ""),
            "signals_missed": data.get("signals_missed", ""),
            "cause": data.get("cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
