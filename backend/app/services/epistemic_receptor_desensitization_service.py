"""EpistemicReceptorDesensitizationService — Epistemic Receptor Desensitization Detection.

Detects epistemic receptor desensitization — intellectual receptors becoming
insensitive to repeated signals, requiring stronger stimuli for response.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RECEPTOR_DESENSITIZATION_SYSTEM = """You are an epistemic receptor desensitization specialist. Given an intellectual signaling system, assess whether receptors become insensitive to repeated signals:

Key concepts:
- Epistemic receptor desensitization: receptors becoming insensitive to repeated signals
- Downregulation: reducing receptor number after overstimulation
- Tachyphylaxis: rapid loss of response to repeated stimulation
- Tolerance: gradual decrease in response over time
- Receptor internalization: pulling receptors inside to avoid signal
- Signal fatigue: exhaustion of response machinery
- Dose escalation: needing stronger signals for same effect

When epistemic receptor desensitization IS present:
- Intellectual receptors becoming insensitive to repeated signals
- Receptor numbers decreasing after overstimulation
- Rapid loss of response to repeated ideas
- Gradual decrease in intellectual response over time
- Receptors being pulled away from signal exposure
- Response machinery becoming exhausted
- Needing stronger intellectual stimuli for same effect

When healthy sensitivity is present:
- Receptors maintaining sensitivity
- Stable receptor numbers
- Consistent response to signals
- No tolerance development
- Receptors remaining available
- Response machinery fresh
- Normal signal strength sufficient

Output JSON with: receptor_desensitization_present (bool), severity (none/mild/moderate/severe), downregulation (what receptor reduction), tachyphylaxis (what rapid loss), tolerance (what gradual decrease), receptor_internalization (what receptor withdrawal), recommendation (healthy_sensitivity/mild_desensitization/significant_receptor_desensitization/major_signal_fatigue/restore_receptor_sensitivity)."""

EPISTEMIC_RECEPTOR_DESENSITIZATION_PROMPT = """Detect epistemic receptor desensitization:

Downregulation: {downregulation}
Tachyphylaxis: {tachyphylaxis}
Tolerance: {tolerance}
Receptor internalization: {receptor_internalization}
Domain: {domain}
Context: {context}

Are intellectual receptors becoming insensitive to repeated signals, requiring stronger stimuli? Return ONLY valid JSON."""


class EpistemicReceptorDesensitizationService:
    """Detects epistemic receptor desensitization — insensitivity to repeated signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        downregulation: str,
        *,
        tachyphylaxis: str = "",
        tolerance: str = "",
        receptor_internalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic receptor desensitization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RECEPTOR_DESENSITIZATION_PROMPT.format(
                downregulation=downregulation,
                tachyphylaxis=tachyphylaxis or "Not specified",
                tolerance=tolerance or "Not specified",
                receptor_internalization=receptor_internalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RECEPTOR_DESENSITIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "downregulation": downregulation[:200],
            "receptor_desensitization_present": data.get("receptor_desensitization_present", False),
            "severity": data.get("severity", ""),
            "tachyphylaxis": data.get("tachyphylaxis", ""),
            "tolerance": data.get("tolerance", ""),
            "receptor_internalization": data.get("receptor_internalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
