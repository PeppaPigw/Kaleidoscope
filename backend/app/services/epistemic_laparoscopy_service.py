"""EpistemicLaparoscopyService — Epistemic Laparoscopy Detection.

Detects need for epistemic laparoscopy — minimally invasive examination
of intellectual cavity to find hidden problems without major disruption.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LAPAROSCOPY_SYSTEM = """You are an epistemic laparoscopy specialist. Given intellectual cavity examination, assess whether hidden problems exist within:

Key concepts:
- Epistemic laparoscopy: minimally invasive intellectual cavity examination
- Adhesion: abnormal connections between structures
- Free fluid: accumulated substance in cavity
- Organ displacement: structures shifted from normal position
- Peritoneal seeding: pathology spreading across cavity surface
- Port site: entry point for examination
- Insufflation: expanding space for visualization

When epistemic laparoscopy findings ARE present:
- Hidden problems within intellectual cavity
- Abnormal connections between structures
- Accumulated substance in intellectual space
- Structures shifted from normal position
- Pathology spreading across cavity surface
- Need for examination entry points
- Need to expand space for visualization

When healthy cavity is present:
- No hidden problems
- Normal structural relationships
- No accumulated substance
- Structures in normal position
- Clean cavity surface
- No examination needed
- Adequate natural space

Output JSON with: laparoscopy_findings_present (bool), severity (none/mild/moderate/severe), adhesions (what abnormal connections), free_fluid (what accumulated substance), organ_displacement (what shifted structures), peritoneal_seeding (what surface spread), recommendation (healthy_cavity/mild_findings/significant_cavity_pathology/major_hidden_disease/intervene_intellectual_cavity)."""

EPISTEMIC_LAPAROSCOPY_PROMPT = """Detect epistemic laparoscopy findings:

Adhesions: {adhesions}
Free fluid: {free_fluid}
Organ displacement: {organ_displacement}
Peritoneal seeding: {peritoneal_seeding}
Domain: {domain}
Context: {context}

Are there hidden problems within the intellectual cavity requiring minimally invasive examination? Return ONLY valid JSON."""


class EpistemicLaparoscopyService:
    """Detects epistemic laparoscopy findings — hidden intellectual cavity problems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        adhesions: str,
        *,
        free_fluid: str = "",
        organ_displacement: str = "",
        peritoneal_seeding: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic laparoscopy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LAPAROSCOPY_PROMPT.format(
                adhesions=adhesions,
                free_fluid=free_fluid or "Not specified",
                organ_displacement=organ_displacement or "Not specified",
                peritoneal_seeding=peritoneal_seeding or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LAPAROSCOPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "adhesions": adhesions[:200],
            "laparoscopy_findings_present": data.get("laparoscopy_findings_present", False),
            "severity": data.get("severity", ""),
            "free_fluid": data.get("free_fluid", ""),
            "organ_displacement": data.get("organ_displacement", ""),
            "peritoneal_seeding": data.get("peritoneal_seeding", ""),
            "recommendation": data.get("recommendation", ""),
        }
