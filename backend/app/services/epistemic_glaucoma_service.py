"""EpistemicGlaucomaService — Epistemic Glaucoma Detection.

Detects epistemic glaucoma — pressure buildup damaging the intellectual
optic nerve, causing progressive loss of peripheral vision.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GLAUCOMA_SYSTEM = """You are an epistemic glaucoma specialist. Given intellectual pressure, assess whether it damages the optic nerve:

Key concepts:
- Epistemic glaucoma: pressure damaging intellectual optic nerve
- Intraocular pressure: internal intellectual pressure level
- Optic disc cupping: nerve head being excavated by pressure
- Visual field loss: progressive loss of peripheral awareness
- Aqueous humor: fluid whose buildup causes pressure
- Trabecular meshwork: drainage system for intellectual pressure
- Angle closure: sudden blockage of pressure drainage

When epistemic glaucoma IS present:
- Pressure buildup damaging intellectual nerve
- Elevated internal intellectual pressure
- Nerve head being excavated by sustained pressure
- Progressive loss of peripheral intellectual awareness
- Fluid buildup causing the pressure
- Drainage system for intellectual pressure failing
- Sudden blockage of pressure relief

When healthy pressure is present:
- Normal intellectual pressure
- No nerve damage
- Intact nerve head
- Full peripheral awareness
- Balanced fluid dynamics
- Functioning drainage
- No angle closure risk

Output JSON with: glaucoma_present (bool), severity (none/mild/moderate/severe), intraocular_pressure (what pressure level), optic_disc_cupping (what nerve excavation), visual_field_loss (what peripheral loss), drainage_failure (what meshwork blockage), recommendation (healthy_pressure/mild_glaucoma/significant_glaucoma/major_nerve_damage/reduce_intellectual_pressure)."""

EPISTEMIC_GLAUCOMA_PROMPT = """Detect epistemic glaucoma:

Intraocular pressure: {intraocular_pressure}
Optic disc cupping: {optic_disc_cupping}
Visual field loss: {visual_field_loss}
Drainage failure: {drainage_failure}
Domain: {domain}
Context: {context}

Is pressure buildup damaging the intellectual optic nerve, causing peripheral vision loss? Return ONLY valid JSON."""


class EpistemicGlaucomaService:
    """Detects epistemic glaucoma — pressure damaging intellectual optic nerve."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intraocular_pressure: str,
        *,
        optic_disc_cupping: str = "",
        visual_field_loss: str = "",
        drainage_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic glaucoma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GLAUCOMA_PROMPT.format(
                intraocular_pressure=intraocular_pressure,
                optic_disc_cupping=optic_disc_cupping or "Not specified",
                visual_field_loss=visual_field_loss or "Not specified",
                drainage_failure=drainage_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GLAUCOMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intraocular_pressure": intraocular_pressure[:200],
            "glaucoma_present": data.get("glaucoma_present", False),
            "severity": data.get("severity", ""),
            "optic_disc_cupping": data.get("optic_disc_cupping", ""),
            "visual_field_loss": data.get("visual_field_loss", ""),
            "drainage_failure": data.get("drainage_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
