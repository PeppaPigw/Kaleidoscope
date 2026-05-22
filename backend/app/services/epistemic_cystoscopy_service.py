"""EpistemicCystoscopyService — Epistemic Cystoscopy Detection.

Detects need for epistemic cystoscopy — examining intellectual storage
and filtration systems for pathology affecting retention and release.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CYSTOSCOPY_SYSTEM = """You are an epistemic cystoscopy specialist. Given intellectual storage systems, assess whether pathology affects retention and release:

Key concepts:
- Epistemic cystoscopy: examining intellectual storage and filtration
- Bladder tumor: growth in storage organ
- Trabeculation: thickened walls from chronic obstruction
- Ureteral orifice: entry point to storage
- Capacity reduction: decreased storage volume
- Reflux: backward flow from storage
- Retention: inability to release stored content

When epistemic cystoscopy findings ARE present:
- Pathology in intellectual storage systems
- Growths in storage organs
- Thickened walls from chronic obstruction
- Compromised entry points
- Decreased storage capacity
- Backward flow from storage
- Inability to release stored intellectual content

When healthy storage is present:
- Normal storage systems
- No growths
- Normal wall thickness
- Clear entry points
- Full storage capacity
- Normal directional flow
- Normal release function

Output JSON with: cystoscopy_findings_present (bool), severity (none/mild/moderate/severe), bladder_tumor (what storage growth), trabeculation (what wall thickening), capacity_reduction (what volume loss), reflux (what backward flow), recommendation (healthy_storage/mild_findings/significant_storage_pathology/major_retention_failure/restore_intellectual_storage)."""

EPISTEMIC_CYSTOSCOPY_PROMPT = """Detect epistemic cystoscopy findings:

Bladder tumor: {bladder_tumor}
Trabeculation: {trabeculation}
Capacity reduction: {capacity_reduction}
Reflux: {reflux}
Domain: {domain}
Context: {context}

Is there pathology in intellectual storage and filtration systems affecting retention? Return ONLY valid JSON."""


class EpistemicCystoscopyService:
    """Detects epistemic cystoscopy findings — intellectual storage pathology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        bladder_tumor: str,
        *,
        trabeculation: str = "",
        capacity_reduction: str = "",
        reflux: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cystoscopy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CYSTOSCOPY_PROMPT.format(
                bladder_tumor=bladder_tumor,
                trabeculation=trabeculation or "Not specified",
                capacity_reduction=capacity_reduction or "Not specified",
                reflux=reflux or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CYSTOSCOPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "bladder_tumor": bladder_tumor[:200],
            "cystoscopy_findings_present": data.get("cystoscopy_findings_present", False),
            "severity": data.get("severity", ""),
            "trabeculation": data.get("trabeculation", ""),
            "capacity_reduction": data.get("capacity_reduction", ""),
            "reflux": data.get("reflux", ""),
            "recommendation": data.get("recommendation", ""),
        }
