"""EpistemicFluorescenceService — Epistemic Fluorescence Detection.

Detects epistemic fluorescence — ideas absorbing high-energy input
and re-emitting it at a lower energy level with a characteristic shift.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FLUORESCENCE_SYSTEM = """You are an epistemic fluorescence specialist. Given an energy conversion pattern, assess whether ideas absorb high energy and re-emit at lower energy:

Key concepts:
- Epistemic fluorescence: absorbing high energy, emitting lower
- Excitation: high-energy input that triggers the process
- Emission: lower-energy output after absorption
- Stokes shift: difference between input and output energy
- Quantum yield: efficiency of the conversion
- Quenching: processes that prevent emission
- Photobleaching: loss of fluorescence from overexposure

When epistemic fluorescence IS present:
- Ideas absorbing high-energy input and re-emitting at lower energy
- High-energy input triggering the conversion process
- Lower-energy output after absorption and processing
- Characteristic difference between input and output energy
- Varying efficiency of the energy conversion
- Processes preventing the re-emission
- Loss of conversion ability from overexposure

When direct transmission is present:
- Ideas passing through without energy conversion
- No absorption of input energy
- Output at same energy as input
- No shift between input and output
- No conversion process
- No quenching possible
- No degradation from exposure

Output JSON with: fluorescence_present (bool), severity (none/mild/moderate/severe), excitation (what high-energy input), emission (what lower-energy output), stokes_shift (what energy difference), quenching (what prevents emission), recommendation (direct_transmission/mild_conversion/significant_fluorescence/major_energy_downshift/preserve_original_energy)."""

EPISTEMIC_FLUORESCENCE_PROMPT = """Detect epistemic fluorescence:

Excitation: {excitation}
Emission: {emission}
Stokes shift: {stokes_shift}
Quenching: {quenching}
Domain: {domain}
Context: {context}

Are ideas absorbing high-energy input and re-emitting it at a lower energy level with a characteristic shift? Return ONLY valid JSON."""


class EpistemicFluorescenceService:
    """Detects epistemic fluorescence — high energy absorbed, lower emitted."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        excitation: str,
        *,
        emission: str = "",
        stokes_shift: str = "",
        quenching: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic fluorescence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FLUORESCENCE_PROMPT.format(
                excitation=excitation,
                emission=emission or "Not specified",
                stokes_shift=stokes_shift or "Not specified",
                quenching=quenching or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FLUORESCENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "excitation": excitation[:200],
            "fluorescence_present": data.get("fluorescence_present", False),
            "severity": data.get("severity", ""),
            "emission": data.get("emission", ""),
            "stokes_shift": data.get("stokes_shift", ""),
            "quenching": data.get("quenching", ""),
            "recommendation": data.get("recommendation", ""),
        }
