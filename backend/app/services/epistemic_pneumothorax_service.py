"""EpistemicPneumothoraxService — Epistemic Pneumothorax Detection.

Detects epistemic pneumothorax — collapse of intellectual space from
pressure imbalance, where external pressure overwhelms internal structure.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PNEUMOTHORAX_SYSTEM = """You are an epistemic pneumothorax specialist. Given intellectual space, assess whether pressure imbalance is causing collapse:

Key concepts:
- Epistemic pneumothorax: collapse of intellectual space from pressure imbalance
- Tension: progressive pressure buildup compressing function
- Pleural breach: break in the boundary allowing pressure leak
- Mediastinal shift: central structures displaced by pressure
- Lung collapse: loss of functional intellectual volume
- Chest tube: drainage to relieve pressure
- Spontaneous: occurring without external trauma

When epistemic pneumothorax IS present:
- Collapse of intellectual space from pressure imbalance
- Progressive pressure buildup compressing function
- Break in boundaries allowing pressure to leak
- Central intellectual structures displaced
- Loss of functional intellectual volume
- Need for drainage to relieve pressure
- Occurring without obvious external cause

When healthy space is present:
- Maintained intellectual space
- Balanced pressures
- Intact boundaries
- Central structures in place
- Full functional volume
- No drainage needed
- Stable without intervention

Output JSON with: pneumothorax_present (bool), severity (none/mild/moderate/severe), tension (what progressive pressure), pleural_breach (what boundary break), mediastinal_shift (what displacement), lung_collapse (what volume loss), recommendation (healthy_space/mild_pneumothorax/significant_pneumothorax/major_space_collapse/relieve_intellectual_pressure)."""

EPISTEMIC_PNEUMOTHORAX_PROMPT = """Detect epistemic pneumothorax:

Tension: {tension}
Pleural breach: {pleural_breach}
Mediastinal shift: {mediastinal_shift}
Lung collapse: {lung_collapse}
Domain: {domain}
Context: {context}

Is intellectual space collapsing from pressure imbalance? Return ONLY valid JSON."""


class EpistemicPneumothoraxService:
    """Detects epistemic pneumothorax — collapse from pressure imbalance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        tension: str,
        *,
        pleural_breach: str = "",
        mediastinal_shift: str = "",
        lung_collapse: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pneumothorax."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PNEUMOTHORAX_PROMPT.format(
                tension=tension,
                pleural_breach=pleural_breach or "Not specified",
                mediastinal_shift=mediastinal_shift or "Not specified",
                lung_collapse=lung_collapse or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PNEUMOTHORAX_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "tension": tension[:200],
            "pneumothorax_present": data.get("pneumothorax_present", False),
            "severity": data.get("severity", ""),
            "pleural_breach": data.get("pleural_breach", ""),
            "mediastinal_shift": data.get("mediastinal_shift", ""),
            "lung_collapse": data.get("lung_collapse", ""),
            "recommendation": data.get("recommendation", ""),
        }
