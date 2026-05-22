"""EpistemicTinnitusService — Epistemic Tinnitus Detection.

Detects epistemic tinnitus — persistent ringing or noise in intellectual
space that isn't from external input, drowning out real signals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TINNITUS_SYSTEM = """You are an epistemic tinnitus specialist. Given persistent intellectual noise without external source, assess tinnitus:

Key concepts:
- Epistemic tinnitus: persistent noise not from external input
- Subjective tinnitus: only the thinker perceives the noise
- Objective tinnitus: noise measurable by others
- Pulsatile: rhythmic noise matching thought patterns
- Masking: using other input to cover the noise
- Habituation: learning to ignore persistent noise
- Hyperawareness: attention amplifying the noise

When epistemic tinnitus IS present:
- Persistent noise without external source
- Only thinker perceives the noise
- Rhythmic noise matching thought patterns
- Unable to mask with other input
- No habituation occurring
- Attention amplifying the noise
- Drowning out real signals

When no tinnitus:
- No persistent internal noise
- Clear intellectual silence available
- No phantom signals
- No masking needed
- Natural habituation working
- Normal attention patterns
- Real signals clearly heard

Output JSON with: tinnitus_detected (bool), severity (none/mild/moderate/severe), noise_type (what sound pattern), source_hypothesis (what origin), masking_effectiveness (what coverage), habituation_status (what adaptation), recommendation (no_tinnitus/mild_habituation_therapy/significant_masking_devices/major_cognitive_behavioral/emergency_acute_onset)."""

EPISTEMIC_TINNITUS_PROMPT = """Detect epistemic tinnitus:

Noise type: {noise_type}
Source hypothesis: {source_hypothesis}
Masking effectiveness: {masking_effectiveness}
Habituation status: {habituation_status}
Domain: {domain}
Context: {context}

Is there persistent noise in intellectual space not from external input? Return ONLY valid JSON."""


class EpistemicTinnitusService:
    """Detects epistemic tinnitus — persistent noise not from external input."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        noise_type: str,
        *,
        source_hypothesis: str = "",
        masking_effectiveness: str = "",
        habituation_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tinnitus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TINNITUS_PROMPT.format(
                noise_type=noise_type,
                source_hypothesis=source_hypothesis or "Not specified",
                masking_effectiveness=masking_effectiveness or "Not specified",
                habituation_status=habituation_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TINNITUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "noise_type": noise_type[:200],
            "tinnitus_detected": data.get("tinnitus_detected", False),
            "severity": data.get("severity", ""),
            "source_hypothesis": data.get("source_hypothesis", ""),
            "masking_effectiveness": data.get("masking_effectiveness", ""),
            "habituation_status": data.get("habituation_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
