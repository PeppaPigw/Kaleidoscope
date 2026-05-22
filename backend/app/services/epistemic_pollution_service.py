"""EpistemicPollutionService — Epistemic Pollution Detection.

Detects epistemic pollution — pollution of the information environment
making good reasoning harder, where noise, misinformation, or
low-quality information degrades the epistemic commons.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POLLUTION_SYSTEM = """You are an epistemic pollution specialist. Given an information environment, assess whether pollution is degrading reasoning quality:

Key concepts:
- Epistemic pollution: information environment degraded
- Noise flooding: signal drowned in noise
- Misinformation saturation: false info making truth harder to find
- Quality degradation: low-quality info displacing high-quality
- Trust erosion: pollution eroding trust in all information
- Reasoning interference: polluted environment making reasoning harder
- Commons degradation: shared information resources degraded

When epistemic pollution IS present:
- Information environment degraded by noise or misinformation
- Signal increasingly hard to find amid noise
- Low-quality information displacing high-quality
- Trust in information sources eroded
- Good reasoning made harder by environment
- Shared epistemic resources degraded
- Information quality declining systematically

When information abundance is appropriate:
- Diverse information serving understanding
- Quality maintained alongside quantity
- Signal distinguishable from noise
- Trust calibrated to source quality
- Environment supporting rather than hindering reasoning
- Epistemic commons maintained
- Information quality stable or improving

Output JSON with: pollution_present (bool), severity (none/mild/moderate/severe), environment (what information environment), pollutants (what pollutes the environment), impact (how reasoning is affected), source (where pollution comes from), recommendation (healthy_environment/mild_noise_increase/significant_epistemic_pollution/major_commons_degradation/protect_epistemic_commons)."""

EPISTEMIC_POLLUTION_PROMPT = """Detect epistemic pollution:

Information environment: {environment}
Pollutants: {pollutants}
Impact on reasoning: {impact}
Quality trends: {trends}
Domain: {domain}
Context: {context}

Is the information environment polluted in ways that make good reasoning harder? Return ONLY valid JSON."""


class EpistemicPollutionService:
    """Detects epistemic pollution — information environment degradation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        pollutants: str = "",
        impact: str = "",
        trends: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pollution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POLLUTION_PROMPT.format(
                environment=environment,
                pollutants=pollutants or "Not specified",
                impact=impact or "Not specified",
                trends=trends or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POLLUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "pollution_present": data.get("pollution_present", False),
            "severity": data.get("severity", ""),
            "pollutants": data.get("pollutants", ""),
            "impact": data.get("impact", ""),
            "source": data.get("source", ""),
            "recommendation": data.get("recommendation", ""),
        }
