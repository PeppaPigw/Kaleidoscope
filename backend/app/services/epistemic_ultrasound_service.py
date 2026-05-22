"""EpistemicUltrasoundService — Epistemic Ultrasound Detection.

Detects need for epistemic ultrasound — real-time dynamic imaging of
intellectual movement and flow patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ULTRASOUND_SYSTEM = """You are an epistemic ultrasound specialist. Given intellectual movement patterns, assess whether dynamic abnormalities exist:

Key concepts:
- Epistemic ultrasound: real-time dynamic imaging of intellectual movement
- Echogenicity: how ideas reflect examination
- Doppler flow: direction and speed of intellectual circulation
- Cystic lesion: fluid-filled abnormal space
- Solid mass: dense abnormal growth
- Shadowing: dense structure blocking deeper visualization
- Vascularity: blood supply to a structure

When epistemic ultrasound findings ARE present:
- Dynamic abnormalities in intellectual movement
- Ideas reflecting examination abnormally
- Abnormal direction or speed of circulation
- Fluid-filled abnormal intellectual spaces
- Dense abnormal intellectual growths
- Dense structures blocking deeper understanding
- Abnormal supply to intellectual structures

When healthy dynamics are present:
- Normal intellectual movement
- Normal reflection patterns
- Normal circulation direction and speed
- No cystic spaces
- No solid masses
- No shadowing
- Normal vascularity

Output JSON with: ultrasound_findings_present (bool), severity (none/mild/moderate/severe), echogenicity (what reflection abnormality), doppler_flow (what circulation change), cystic_lesion (what fluid space), solid_mass (what dense growth), recommendation (healthy_dynamics/mild_findings/significant_dynamic_pathology/major_movement_disease/address_intellectual_flow_abnormality)."""

EPISTEMIC_ULTRASOUND_PROMPT = """Detect epistemic ultrasound findings:

Echogenicity: {echogenicity}
Doppler flow: {doppler_flow}
Cystic lesion: {cystic_lesion}
Solid mass: {solid_mass}
Domain: {domain}
Context: {context}

Are there dynamic abnormalities in intellectual movement and flow? Return ONLY valid JSON."""


class EpistemicUltrasoundService:
    """Detects epistemic ultrasound findings — dynamic intellectual movement abnormalities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        echogenicity: str,
        *,
        doppler_flow: str = "",
        cystic_lesion: str = "",
        solid_mass: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic ultrasound findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ULTRASOUND_PROMPT.format(
                echogenicity=echogenicity,
                doppler_flow=doppler_flow or "Not specified",
                cystic_lesion=cystic_lesion or "Not specified",
                solid_mass=solid_mass or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ULTRASOUND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "echogenicity": echogenicity[:200],
            "ultrasound_findings_present": data.get("ultrasound_findings_present", False),
            "severity": data.get("severity", ""),
            "doppler_flow": data.get("doppler_flow", ""),
            "cystic_lesion": data.get("cystic_lesion", ""),
            "solid_mass": data.get("solid_mass", ""),
            "recommendation": data.get("recommendation", ""),
        }
