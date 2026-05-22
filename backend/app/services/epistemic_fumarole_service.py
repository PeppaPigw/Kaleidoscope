"""EpistemicFumaroleService — Epistemic Fumarole Detection.

Detects epistemic fumaroles — vents releasing hot gases that signal
deeper intellectual activity beneath the surface.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FUMAROLE_SYSTEM = """You are an epistemic fumarole specialist. Given intellectual signals, assess whether surface vents indicate deeper activity:

Key concepts:
- Epistemic fumarole: surface vent signaling deeper activity
- Hot gas: heated intellectual output escaping through vents
- Deep activity: significant intellectual processes beneath surface
- Signal: surface manifestation of underground processes
- Sulfur: toxic byproducts in the vented material
- Monitoring: watching fumaroles for eruption prediction
- Geothermal: harnessing the energy from vents productively

When epistemic fumarole IS present:
- Surface vents releasing hot intellectual gases
- Heated intellectual output escaping through narrow openings
- Significant intellectual processes occurring beneath surface
- Surface manifestations signaling underground activity
- Toxic byproducts mixed with vented material
- Vents useful for monitoring deeper processes
- Potential to harness the energy productively

When quiet surface is present:
- No surface vents or emissions
- No heated output escaping
- No significant underground processes
- Surface accurately representing subsurface state
- No toxic byproducts venting
- No monitoring needed
- No geothermal energy to harness

Output JSON with: fumarole_present (bool), severity (none/mild/moderate/severe), vents (what surface vents exist), deep_activity (what deeper processes occur), signal (what the vents signal), toxicity (what toxic byproducts vent), recommendation (quiet_surface/mild_venting/significant_fumarole/major_deep_activity/monitor_and_harness_energy)."""

EPISTEMIC_FUMAROLE_PROMPT = """Detect epistemic fumarole:

Vents: {vents}
Deep activity: {deep_activity}
Signal: {signal}
Toxicity: {toxicity}
Domain: {domain}
Context: {context}

Are surface vents releasing hot gases that signal deeper intellectual activity beneath? Return ONLY valid JSON."""


class EpistemicFumaroleService:
    """Detects epistemic fumaroles — surface vents signaling deeper activity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        vents: str,
        *,
        deep_activity: str = "",
        signal: str = "",
        toxicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fumarole."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FUMAROLE_PROMPT.format(
                vents=vents,
                deep_activity=deep_activity or "Not specified",
                signal=signal or "Not specified",
                toxicity=toxicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FUMAROLE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "vents": vents[:200],
            "fumarole_present": data.get("fumarole_present", False),
            "severity": data.get("severity", ""),
            "deep_activity": data.get("deep_activity", ""),
            "signal": data.get("signal", ""),
            "toxicity": data.get("toxicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
