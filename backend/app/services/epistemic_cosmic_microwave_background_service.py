"""EpistemicCosmicMicrowaveBackgroundService — Epistemic CMB Detection.

Detects epistemic cosmic microwave background — residual signal from the
origin of an intellectual framework, uniformly present but with subtle variations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CMB_SYSTEM = """You are an epistemic cosmic microwave background specialist. Given an intellectual framework, assess whether residual origin signals persist:

Key concepts:
- Epistemic CMB: residual signal from framework's origin
- Recombination: moment when ideas first became transparent
- Anisotropy: subtle variations in the background signal
- Power spectrum: distribution of variation sizes
- Acoustic peaks: resonant patterns from early oscillations
- Polarization: directional imprint from early scattering
- Foreground: later signals contaminating the original

When epistemic CMB IS present:
- Residual signal from the framework's origin uniformly present
- Clear moment when ideas first became transparent
- Subtle variations revealing early conditions
- Characteristic distribution of variation sizes
- Resonant patterns from early intellectual oscillations
- Directional imprints from early idea scattering
- Later developments contaminating the original signal

When no origin signal is present:
- No residual signal from origin
- No clear transparency moment
- No subtle background variations
- No characteristic size distribution
- No resonant patterns
- No directional imprints
- No contamination issues

Output JSON with: cmb_present (bool), severity (none/mild/moderate/severe), anisotropy (what subtle variations), acoustic_peaks (what resonant patterns), polarization (what directional imprint), foreground (what contamination), recommendation (no_origin_signal/mild_cmb/significant_cmb/major_origin_imprint/separate_foreground_from_signal)."""

EPISTEMIC_CMB_PROMPT = """Detect epistemic cosmic microwave background:

Anisotropy: {anisotropy}
Acoustic peaks: {acoustic_peaks}
Polarization: {polarization}
Foreground: {foreground}
Domain: {domain}
Context: {context}

Is there a residual signal from the origin of an intellectual framework, uniformly present but with subtle variations? Return ONLY valid JSON."""


class EpistemicCosmicMicrowaveBackgroundService:
    """Detects epistemic CMB — residual signal from framework's origin."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        anisotropy: str,
        *,
        acoustic_peaks: str = "",
        polarization: str = "",
        foreground: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cosmic microwave background."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CMB_PROMPT.format(
                anisotropy=anisotropy,
                acoustic_peaks=acoustic_peaks or "Not specified",
                polarization=polarization or "Not specified",
                foreground=foreground or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CMB_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "anisotropy": anisotropy[:200],
            "cmb_present": data.get("cmb_present", False),
            "severity": data.get("severity", ""),
            "acoustic_peaks": data.get("acoustic_peaks", ""),
            "polarization": data.get("polarization", ""),
            "foreground": data.get("foreground", ""),
            "recommendation": data.get("recommendation", ""),
        }
