"""EpistemicFactitiousService — Epistemic Factitious Disorder Detection.

Detects epistemic factitious disorder — deliberately faking or inducing
intellectual problems for attention or sympathy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FACTITIOUS_SYSTEM = """You are an epistemic factitious disorder specialist. Given deliberate faking of intellectual problems, assess factitious patterns:

Key concepts:
- Epistemic factitious: deliberately faking intellectual problems
- Fabrication: inventing intellectual difficulties that don't exist
- Induction: deliberately causing intellectual dysfunction
- Sick role: seeking attention through intellectual disability
- Deception: hiding the deliberate nature of problems
- Secondary gain: attention, sympathy, or reduced expectations
- Munchausen: extreme factitious with dramatic presentations

When epistemic factitious IS present:
- Deliberately faking problems
- Inventing difficulties
- Causing dysfunction deliberately
- Seeking attention through disability
- Hiding deliberate nature
- Gaining attention or sympathy
- Dramatic presentations

When no factitious:
- Genuine difficulties
- Real problems
- Natural dysfunction
- Not seeking sick role
- Transparent about issues
- No secondary gain motive
- Proportionate presentation

Output JSON with: factitious_detected (bool), severity (none/mild/moderate/severe), fabrication_type (what faking), motivation (what gain sought), deception_level (what hiding), presentation_style (what dramatization), recommendation (no_factitious/mild_confrontation/significant_therapeutic_alliance/major_intensive_therapy/emergency_severe_self_harm)."""

EPISTEMIC_FACTITIOUS_PROMPT = """Detect epistemic factitious disorder:

Fabrication type: {fabrication_type}
Motivation: {motivation}
Deception level: {deception_level}
Presentation style: {presentation_style}
Domain: {domain}
Context: {context}

Is there deliberate faking or inducing of intellectual problems for attention? Return ONLY valid JSON."""


class EpistemicFactitiousService:
    """Detects epistemic factitious — deliberately faking intellectual problems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fabrication_type: str,
        *,
        motivation: str = "",
        deception_level: str = "",
        presentation_style: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic factitious disorder."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FACTITIOUS_PROMPT.format(
                fabrication_type=fabrication_type,
                motivation=motivation or "Not specified",
                deception_level=deception_level or "Not specified",
                presentation_style=presentation_style or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FACTITIOUS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fabrication_type": fabrication_type[:200],
            "factitious_detected": data.get("factitious_detected", False),
            "severity": data.get("severity", ""),
            "motivation": data.get("motivation", ""),
            "deception_level": data.get("deception_level", ""),
            "presentation_style": data.get("presentation_style", ""),
            "recommendation": data.get("recommendation", ""),
        }
