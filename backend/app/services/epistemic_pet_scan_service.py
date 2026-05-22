"""EpistemicPetScanService — Epistemic PET Scan Detection.

Detects need for epistemic PET scan — metabolic activity imaging showing
intellectual hotspots of abnormal energy consumption.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PET_SCAN_SYSTEM = """You are an epistemic PET scan specialist. Given intellectual metabolic patterns, assess whether abnormal activity hotspots exist:

Key concepts:
- Epistemic PET scan: metabolic activity imaging of intellectual hotspots
- Hypermetabolic focus: area consuming excessive intellectual energy
- Hypometabolic region: area with abnormally low activity
- SUV uptake: standardized measure of activity intensity
- Metastatic pattern: multiple scattered hotspots suggesting spread
- Treatment response: change in activity after intervention
- False positive: benign cause of increased activity

When epistemic PET scan findings ARE present:
- Abnormal activity hotspots in intellectual system
- Areas consuming excessive intellectual energy
- Areas with abnormally low activity
- High intensity activity in focal areas
- Multiple scattered hotspots suggesting spread
- Changes in activity after intervention
- Need to distinguish true from false positives

When healthy metabolism is present:
- Normal activity distribution
- Proportionate energy consumption
- No hypometabolic regions
- Normal intensity levels
- No scattered hotspots
- Stable activity patterns
- No false positive concerns

Output JSON with: pet_findings_present (bool), severity (none/mild/moderate/severe), hypermetabolic_focus (what excessive energy area), hypometabolic_region (what low activity area), metastatic_pattern (what scattered spread), treatment_response (what intervention change), recommendation (healthy_metabolism/mild_findings/significant_metabolic_pathology/major_activity_disease/address_intellectual_metabolic_hotspots)."""

EPISTEMIC_PET_SCAN_PROMPT = """Detect epistemic PET scan findings:

Hypermetabolic focus: {hypermetabolic_focus}
Hypometabolic region: {hypometabolic_region}
Metastatic pattern: {metastatic_pattern}
Treatment response: {treatment_response}
Domain: {domain}
Context: {context}

Are there abnormal metabolic activity hotspots in the intellectual system? Return ONLY valid JSON."""


class EpistemicPetScanService:
    """Detects epistemic PET scan findings — intellectual metabolic hotspots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hypermetabolic_focus: str,
        *,
        hypometabolic_region: str = "",
        metastatic_pattern: str = "",
        treatment_response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic PET scan findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PET_SCAN_PROMPT.format(
                hypermetabolic_focus=hypermetabolic_focus,
                hypometabolic_region=hypometabolic_region or "Not specified",
                metastatic_pattern=metastatic_pattern or "Not specified",
                treatment_response=treatment_response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PET_SCAN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hypermetabolic_focus": hypermetabolic_focus[:200],
            "pet_findings_present": data.get("pet_findings_present", False),
            "severity": data.get("severity", ""),
            "hypometabolic_region": data.get("hypometabolic_region", ""),
            "metastatic_pattern": data.get("metastatic_pattern", ""),
            "treatment_response": data.get("treatment_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
