"""EpistemicPhononService — Epistemic Phonon Detection.

Detects epistemic phonon — collective vibrations propagating through an
intellectual lattice, carrying information as quantized sound.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PHONON_SYSTEM = """You are an epistemic phonon specialist. Given an intellectual lattice, assess whether collective vibrations propagate through it:

Key concepts:
- Epistemic phonon: collective vibrations in intellectual lattice
- Acoustic mode: all ideas moving in phase (sound-like)
- Optical mode: adjacent ideas moving out of phase
- Dispersion relation: frequency depending on wavelength
- Brillouin zone: allowed wavelength range in the lattice
- Debye temperature: temperature scale for vibrations
- Anharmonicity: vibrations interacting with each other

When epistemic phonon IS present:
- Collective vibrations propagating through intellectual structure
- All ideas moving together in phase (acoustic)
- Adjacent ideas moving against each other (optical)
- Frequency depending on the wavelength of disturbance
- Allowed range of wavelengths in the structure
- Characteristic temperature scale for vibrations
- Vibrations interacting and scattering off each other

When no collective vibration is present:
- No collective propagation
- No in-phase motion
- No out-of-phase motion
- No dispersion
- No wavelength constraints
- No characteristic temperature
- No vibration interactions

Output JSON with: phonon_present (bool), severity (none/mild/moderate/severe), acoustic_mode (what in-phase motion), optical_mode (what out-of-phase motion), dispersion (what frequency-wavelength relation), anharmonicity (what vibration interaction), recommendation (no_vibration/mild_phonon/significant_phonon/major_lattice_vibration/exploit_phonon_modes)."""

EPISTEMIC_PHONON_PROMPT = """Detect epistemic phonon:

Acoustic mode: {acoustic_mode}
Optical mode: {optical_mode}
Dispersion: {dispersion}
Anharmonicity: {anharmonicity}
Domain: {domain}
Context: {context}

Are collective vibrations propagating through an intellectual lattice, carrying information as quantized disturbances? Return ONLY valid JSON."""


class EpistemicPhononService:
    """Detects epistemic phonon — collective vibrations in intellectual lattice."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        acoustic_mode: str,
        *,
        optical_mode: str = "",
        dispersion: str = "",
        anharmonicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic phonon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PHONON_PROMPT.format(
                acoustic_mode=acoustic_mode,
                optical_mode=optical_mode or "Not specified",
                dispersion=dispersion or "Not specified",
                anharmonicity=anharmonicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PHONON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "acoustic_mode": acoustic_mode[:200],
            "phonon_present": data.get("phonon_present", False),
            "severity": data.get("severity", ""),
            "optical_mode": data.get("optical_mode", ""),
            "dispersion": data.get("dispersion", ""),
            "anharmonicity": data.get("anharmonicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
