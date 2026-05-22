"""EpistemicMonocultureDeeperService — Epistemic Monoculture (Deeper) Detection.

Detects dangerous epistemic monoculture — lack of intellectual
diversity creating systemic fragility and blind spots.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MONOCULTURE_DEEPER_SYSTEM = """You are an epistemic monoculture specialist. Given an intellectual environment, assess whether dangerous lack of diversity creates systemic fragility:

Key concepts:
- Epistemic monoculture: dangerous lack of intellectual diversity
- Systemic fragility: fragility from homogeneous thinking
- Blind spot amplification: shared blind spots amplified by uniformity
- Resilience failure: inability to adapt when challenged
- Groupthink ecosystem: entire ecosystem thinking alike
- Innovation starvation: no diversity to generate new ideas
- Catastrophic vulnerability: vulnerability to single-point failure

When epistemic monoculture IS present:
- Dangerous lack of intellectual diversity
- Systemic fragility from homogeneous thinking
- Shared blind spots amplified by uniformity
- Inability to adapt when assumptions challenged
- Entire ecosystem thinking alike
- No diversity to generate genuinely new ideas
- Vulnerable to catastrophic single-point failure

When healthy consensus is present:
- Agreement based on convergent evidence
- Diversity of approaches leading to shared conclusions
- Consensus maintained alongside dissent channels
- Ability to adapt when evidence changes
- Agreement coexisting with productive disagreement
- Innovation still possible within consensus
- Resilience through tested agreement

Output JSON with: monoculture_present (bool), severity (none/mild/moderate/severe), environment (what environment), uniformity (what uniformity exists), fragility (what fragility results), blind_spots (what blind spots are amplified), recommendation (healthy_consensus/mild_uniformity/significant_monoculture/major_systemic_fragility/cultivate_intellectual_diversity)."""

EPISTEMIC_MONOCULTURE_DEEPER_PROMPT = """Detect epistemic monoculture:

Environment: {environment}
Uniformity: {uniformity}
Fragility: {fragility}
Blind spots: {blind_spots}
Domain: {domain}
Context: {context}

Is dangerous lack of intellectual diversity creating systemic fragility? Return ONLY valid JSON."""


class EpistemicMonocultureDeeperService:
    """Detects epistemic monoculture — dangerous lack of intellectual diversity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        uniformity: str = "",
        fragility: str = "",
        blind_spots: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic monoculture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MONOCULTURE_DEEPER_PROMPT.format(
                environment=environment,
                uniformity=uniformity or "Not specified",
                fragility=fragility or "Not specified",
                blind_spots=blind_spots or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MONOCULTURE_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "monoculture_present": data.get("monoculture_present", False),
            "severity": data.get("severity", ""),
            "uniformity": data.get("uniformity", ""),
            "fragility": data.get("fragility", ""),
            "blind_spots": data.get("blind_spots", ""),
            "recommendation": data.get("recommendation", ""),
        }
