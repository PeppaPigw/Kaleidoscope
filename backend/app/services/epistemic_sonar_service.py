"""EpistemicSonarService — Epistemic Sonar Detection.

Detects epistemic sonar — using intellectual echoes to map
invisible structures in dark knowledge environments.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SONAR_SYSTEM = """You are an epistemic sonar specialist. Given an intellectual mapping attempt, assess whether echoes are being used to map invisible structures:

Key concepts:
- Epistemic sonar: using echoes to map invisible structures
- Ping: sending out intellectual probes
- Echo: return signal revealing structure
- Resolution: how detailed the mapping is
- Blind spot: areas that don't return echoes
- False echo: misleading return signals
- Depth sounding: measuring how deep knowledge goes

When epistemic sonar IS present:
- Using intellectual echoes to map invisible structures
- Sending out probes to detect hidden features
- Return signals revealing otherwise invisible structure
- Varying resolution of the intellectual mapping
- Areas that don't return echoes remaining unknown
- Misleading return signals creating false maps
- Measuring depth of knowledge through echo timing

When direct observation is present:
- Structures directly visible without echoes
- No need for probing to detect features
- Direct observation rather than inference
- High resolution through direct viewing
- No blind spots from echo failure
- No false signals to mislead
- Depth directly measurable

Output JSON with: sonar_present (bool), severity (none/mild/moderate/severe), probes (what intellectual probes are sent), echoes (what return signals reveal), blind_spots (what areas don't return echoes), false_echoes (what misleading signals exist), recommendation (direct_observation/mild_probing/significant_sonar/major_echo_mapping/verify_echoes_against_reality)."""

EPISTEMIC_SONAR_PROMPT = """Detect epistemic sonar:

Probes: {probes}
Echoes: {echoes}
Blind spots: {blind_spots}
False echoes: {false_echoes}
Domain: {domain}
Context: {context}

Are intellectual echoes being used to map invisible structures in dark knowledge environments? Return ONLY valid JSON."""


class EpistemicSonarService:
    """Detects epistemic sonar — using echoes to map invisible structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        probes: str,
        *,
        echoes: str = "",
        blind_spots: str = "",
        false_echoes: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sonar."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SONAR_PROMPT.format(
                probes=probes,
                echoes=echoes or "Not specified",
                blind_spots=blind_spots or "Not specified",
                false_echoes=false_echoes or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SONAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "probes": probes[:200],
            "sonar_present": data.get("sonar_present", False),
            "severity": data.get("severity", ""),
            "echoes": data.get("echoes", ""),
            "blind_spots": data.get("blind_spots", ""),
            "false_echoes": data.get("false_echoes", ""),
            "recommendation": data.get("recommendation", ""),
        }
