"""EpistemicReverbService — Epistemic Reverb Detection.

Detects epistemic reverb — ideas persisting as echoes in intellectual
spaces long after the original signal has stopped.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_REVERB_SYSTEM = """You are an epistemic reverb specialist. Given an idea persistence pattern, assess whether ideas persist as echoes after the original signal stops:

Key concepts:
- Epistemic reverb: ideas persisting as echoes after source stops
- Decay time: how long echoes persist
- Early reflections: first bounces off nearby surfaces
- Late reverb: diffuse echoes from distant surfaces
- Absorption: surfaces that reduce echo energy
- Flutter echo: rapid repetition between parallel surfaces
- Dead room: space with no reverb at all

When epistemic reverb IS present:
- Ideas persisting as echoes after original signal stops
- Echoes taking time to decay
- First reflections from nearby intellectual surfaces
- Diffuse echoes from distant intellectual surfaces
- Some surfaces absorbing echo energy
- Rapid repetition between parallel intellectual surfaces
- Ideas heard long after they were originally stated

When anechoic clarity is present:
- Ideas heard only once, no echoes
- No persistence after signal stops
- No reflections from surfaces
- No diffuse echoes
- All surfaces fully absorbing
- No repetition between surfaces
- Ideas clear and non-repeating

Output JSON with: reverb_present (bool), severity (none/mild/moderate/severe), decay_time (how long echoes persist), reflections (what surfaces reflect), absorption (what reduces echoes), flutter (what rapid repetition), recommendation (anechoic_clarity/mild_reverb/significant_reverb/major_echo_persistence/add_absorption)."""

EPISTEMIC_REVERB_PROMPT = """Detect epistemic reverb:

Decay time: {decay_time}
Reflections: {reflections}
Absorption: {absorption}
Flutter: {flutter}
Domain: {domain}
Context: {context}

Are ideas persisting as echoes in intellectual spaces long after the original signal has stopped? Return ONLY valid JSON."""


class EpistemicReverbService:
    """Detects epistemic reverb — ideas persisting as echoes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decay_time: str,
        *,
        reflections: str = "",
        absorption: str = "",
        flutter: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic reverb."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_REVERB_PROMPT.format(
                decay_time=decay_time,
                reflections=reflections or "Not specified",
                absorption=absorption or "Not specified",
                flutter=flutter or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_REVERB_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decay_time": decay_time[:200],
            "reverb_present": data.get("reverb_present", False),
            "severity": data.get("severity", ""),
            "reflections": data.get("reflections", ""),
            "absorption": data.get("absorption", ""),
            "flutter": data.get("flutter", ""),
            "recommendation": data.get("recommendation", ""),
        }
