"""EpistemicEcologyInformationPollutionService - Information Pollution Detection.

Detects information pollution degrading the epistemic environment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECOLOGY_INFORMATION_POLLUTION_SYSTEM = """You are an epistemic ecology information pollution specialist. Given signal-noise degradation, assess whether information pollution is degrading the epistemic environment:

Key concepts:
- Information pollution: degraded informational conditions that make reliable knowing harder
- Signal-noise degradation: reliable signals becoming harder to distinguish from noise
- Misinformation flooding: false or low-quality claims overwhelming corrective capacity
- Attention contamination: attention captured by epistemically harmful material
- Trust erosion: confidence in reliable sources and practices being degraded

When information pollution IS present:
- Noise overwhelms reliable signal
- Misinformation floods the environment
- Attention is contaminated by low-quality or manipulative content
- Trust in reliable knowledge channels erodes
- The epistemic environment becomes harder to navigate

When no information pollution:
- Reliable signals remain distinguishable
- Misinformation is limited or corrected
- Attention remains oriented toward epistemic quality
- Trust is calibrated rather than broadly eroded
- The epistemic environment supports reliable inquiry

Output JSON with: pollution_detected (bool), severity (none/mild/moderate/severe), misinformation_flooding (how misinformation floods the environment), attention_contamination (how attention is contaminated), trust_erosion (how trust is eroded), recommendation (no_pollution/mild_signal_restoration/significant_pollution_control/major_environment_cleanup/emergency_epistemic_sanitation)."""

EPISTEMIC_ECOLOGY_INFORMATION_POLLUTION_PROMPT = """Detect epistemic ecology information pollution:

Signal-noise degradation: {signal_noise_degradation}
Misinformation flooding: {misinformation_flooding}
Attention contamination: {attention_contamination}
Trust erosion: {trust_erosion}
Domain: {domain}
Context: {context}

Is information pollution degrading the epistemic environment? Return ONLY valid JSON."""


class EpistemicEcologyInformationPollutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        signal_noise_degradation: str,
        *,
        misinformation_flooding: str = "",
        attention_contamination: str = "",
        trust_erosion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECOLOGY_INFORMATION_POLLUTION_PROMPT.format(
                signal_noise_degradation=signal_noise_degradation,
                misinformation_flooding=misinformation_flooding or "Not specified",
                attention_contamination=attention_contamination or "Not specified",
                trust_erosion=trust_erosion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECOLOGY_INFORMATION_POLLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "signal_noise_degradation": signal_noise_degradation[:200],
            "pollution_detected": data.get("pollution_detected", False),
            "severity": data.get("severity", ""),
            "misinformation_flooding": data.get("misinformation_flooding", ""),
            "attention_contamination": data.get("attention_contamination", ""),
            "trust_erosion": data.get("trust_erosion", ""),
            "recommendation": data.get("recommendation", ""),
        }
