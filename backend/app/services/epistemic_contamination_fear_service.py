"""EpistemicContaminationFearService — Epistemic Contamination Fear Detection.

Detects epistemic contamination fear — fear of intellectual contamination
from exposure to 'impure' or 'dangerous' ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CONTAMINATION_FEAR_SYSTEM = """You are an epistemic contamination fear specialist. Given fear of intellectual contamination, assess contamination anxiety:

Key concepts:
- Epistemic contamination fear: fear of being polluted by ideas
- Purity maintenance: keeping intellectual space clean
- Avoidance: refusing exposure to certain ideas
- Decontamination rituals: mental cleansing after exposure
- Contagion belief: ideas can infect and corrupt
- Boundary rigidity: extreme separation of acceptable/unacceptable
- Disgust response: visceral rejection of contaminating ideas

When epistemic contamination fear IS present:
- Fear of being polluted by ideas
- Keeping intellectual space clean
- Refusing exposure
- Mental cleansing after exposure
- Believing ideas infect
- Extreme separation
- Visceral rejection

When no contamination fear:
- Comfortable with diverse ideas
- Open intellectual space
- Willing to explore
- No cleansing needed
- Ideas as information
- Flexible boundaries
- Neutral engagement

Output JSON with: contamination_fear_detected (bool), severity (none/mild/moderate/severe), purity_maintenance (what keeping clean), avoidance_pattern (what refusing), decontamination_ritual (what cleansing), contagion_belief (what infecting), recommendation (no_contamination_fear/mild_exposure_practice/significant_tolerance_building/major_intensive_erp/emergency_severe_contamination_ocd)."""

EPISTEMIC_CONTAMINATION_FEAR_PROMPT = """Detect epistemic contamination fear:

Purity maintenance: {purity_maintenance}
Avoidance pattern: {avoidance_pattern}
Decontamination ritual: {decontamination_ritual}
Contagion belief: {contagion_belief}
Domain: {domain}
Context: {context}

Is there fear of intellectual contamination from exposure to certain ideas? Return ONLY valid JSON."""


class EpistemicContaminationFearService:
    """Detects epistemic contamination fear — fear of intellectual pollution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        purity_maintenance: str,
        *,
        avoidance_pattern: str = "",
        decontamination_ritual: str = "",
        contagion_belief: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic contamination fear."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CONTAMINATION_FEAR_PROMPT.format(
                purity_maintenance=purity_maintenance,
                avoidance_pattern=avoidance_pattern or "Not specified",
                decontamination_ritual=decontamination_ritual or "Not specified",
                contagion_belief=contagion_belief or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CONTAMINATION_FEAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "purity_maintenance": purity_maintenance[:200],
            "contamination_fear_detected": data.get("contamination_fear_detected", False),
            "severity": data.get("severity", ""),
            "avoidance_pattern": data.get("avoidance_pattern", ""),
            "decontamination_ritual": data.get("decontamination_ritual", ""),
            "contagion_belief": data.get("contagion_belief", ""),
            "recommendation": data.get("recommendation", ""),
        }
