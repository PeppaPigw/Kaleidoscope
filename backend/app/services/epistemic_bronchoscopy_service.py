"""EpistemicBronchoscopyService — Epistemic Bronchoscopy Detection.

Detects need for epistemic bronchoscopy — visualizing intellectual airway
obstructions that impede the flow of ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BRONCHOSCOPY_SYSTEM = """You are an epistemic bronchoscopy specialist. Given intellectual airway patterns, assess whether obstructions impede idea flow:

Key concepts:
- Epistemic bronchoscopy: visualizing intellectual airway obstructions
- Endobronchial mass: growth blocking airway
- Mucus plugging: accumulated debris blocking flow
- Airway collapse: structural failure of idea conduit
- Foreign body: external object lodged in airway
- Granulation tissue: excessive healing blocking passage
- Bronchoalveolar lavage: washing out accumulated debris

When epistemic bronchoscopy findings ARE present:
- Obstructions impeding idea flow
- Growths blocking intellectual airways
- Accumulated debris blocking flow
- Structural failure of idea conduits
- External objects lodged in pathways
- Excessive healing blocking passage
- Need to wash out accumulated debris

When healthy airways are present:
- Clear unobstructed idea flow
- No growths in airways
- No debris accumulation
- Strong structural conduits
- No foreign bodies
- Normal healing
- Clean passages

Output JSON with: bronchoscopy_findings_present (bool), severity (none/mild/moderate/severe), endobronchial_mass (what growth blocking), mucus_plugging (what debris), airway_collapse (what structural failure), foreign_body (what lodged object), recommendation (healthy_airways/mild_findings/significant_obstruction/major_airway_blockage/clear_intellectual_airways)."""

EPISTEMIC_BRONCHOSCOPY_PROMPT = """Detect epistemic bronchoscopy findings:

Endobronchial mass: {endobronchial_mass}
Mucus plugging: {mucus_plugging}
Airway collapse: {airway_collapse}
Foreign body: {foreign_body}
Domain: {domain}
Context: {context}

Are there obstructions impeding the flow of ideas through intellectual airways? Return ONLY valid JSON."""


class EpistemicBronchoscopyService:
    """Detects epistemic bronchoscopy findings — intellectual airway obstructions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        endobronchial_mass: str,
        *,
        mucus_plugging: str = "",
        airway_collapse: str = "",
        foreign_body: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bronchoscopy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BRONCHOSCOPY_PROMPT.format(
                endobronchial_mass=endobronchial_mass,
                mucus_plugging=mucus_plugging or "Not specified",
                airway_collapse=airway_collapse or "Not specified",
                foreign_body=foreign_body or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BRONCHOSCOPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "endobronchial_mass": endobronchial_mass[:200],
            "bronchoscopy_findings_present": data.get("bronchoscopy_findings_present", False),
            "severity": data.get("severity", ""),
            "mucus_plugging": data.get("mucus_plugging", ""),
            "airway_collapse": data.get("airway_collapse", ""),
            "foreign_body": data.get("foreign_body", ""),
            "recommendation": data.get("recommendation", ""),
        }
