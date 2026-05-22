"""EpistemicBandGapService — Epistemic Band Gap Detection.

Detects epistemic band gap — an energy barrier between intellectual
states that prevents ideas from transitioning without sufficient activation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BAND_GAP_SYSTEM = """You are an epistemic band gap specialist. Given an idea transition pattern, assess whether energy barriers prevent state transitions:

Key concepts:
- Epistemic band gap: energy barrier between intellectual states
- Valence band: occupied lower energy state
- Conduction band: higher energy state enabling movement
- Forbidden zone: energy range where no states exist
- Doping: adding impurities to reduce the gap
- Photon absorption: single event providing enough energy
- Thermal excitation: gradual energy accumulation

When epistemic band gap IS present:
- Energy barrier preventing ideas from transitioning between states
- Lower energy state where ideas are stuck
- Higher energy state enabling intellectual movement
- Energy range where no intellectual states exist
- Adding impurities to reduce the transition barrier
- Single events providing enough energy to cross
- Gradual accumulation sometimes crossing the barrier

When continuous spectrum is present:
- No energy barrier between states
- Ideas freely transitioning between levels
- No forbidden energy ranges
- Smooth continuum of states
- No need for impurities
- No threshold events needed
- Gradual transitions always possible

Output JSON with: band_gap_present (bool), severity (none/mild/moderate/severe), valence (what lower state), conduction (what higher state), forbidden (what gap exists), doping (what reduces barrier), recommendation (continuous_spectrum/mild_gap/significant_band_gap/major_energy_barrier/reduce_gap_through_doping)."""

EPISTEMIC_BAND_GAP_PROMPT = """Detect epistemic band gap:

Valence: {valence}
Conduction: {conduction}
Forbidden: {forbidden}
Doping: {doping}
Domain: {domain}
Context: {context}

Is an energy barrier between intellectual states preventing ideas from transitioning without sufficient activation? Return ONLY valid JSON."""


class EpistemicBandGapService:
    """Detects epistemic band gap — energy barrier between states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        valence: str,
        *,
        conduction: str = "",
        forbidden: str = "",
        doping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic band gap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BAND_GAP_PROMPT.format(
                valence=valence,
                conduction=conduction or "Not specified",
                forbidden=forbidden or "Not specified",
                doping=doping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BAND_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "valence": valence[:200],
            "band_gap_present": data.get("band_gap_present", False),
            "severity": data.get("severity", ""),
            "conduction": data.get("conduction", ""),
            "forbidden": data.get("forbidden", ""),
            "doping": data.get("doping", ""),
            "recommendation": data.get("recommendation", ""),
        }
