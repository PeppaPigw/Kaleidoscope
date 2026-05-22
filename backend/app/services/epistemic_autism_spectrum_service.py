"""EpistemicAutismSpectrumService — Epistemic Autism Spectrum Detection.

Detects epistemic autism spectrum — rigid intellectual patterns with
intense focused interests and difficulty with intellectual flexibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTISM_SPECTRUM_SYSTEM = """You are an epistemic autism spectrum specialist. Given rigid intellectual patterns, assess spectrum features:

Key concepts:
- Epistemic autism spectrum: rigid intellectual patterns with intense focus
- Special interests: deep narrow expertise at expense of breadth
- Rigidity: difficulty changing intellectual approach
- Sensory overload: overwhelmed by information complexity
- Social communication: difficulty with intellectual exchange norms
- Systemizing: preference for rule-based intellectual frameworks
- Monotropism: single-channel intellectual attention

When epistemic autism spectrum IS present:
- Rigid intellectual patterns
- Deep narrow expertise
- Difficulty changing approach
- Overwhelmed by complexity
- Difficulty with exchange norms
- Preference for rule-based frameworks
- Single-channel attention

When no spectrum features:
- Flexible intellectual patterns
- Balanced breadth and depth
- Adaptable approach
- Comfortable with complexity
- Natural exchange norms
- Comfortable with ambiguity
- Multi-channel attention

Output JSON with: spectrum_detected (bool), severity (none/mild/moderate/severe), rigidity_level (what inflexibility), special_interest_pattern (what narrow focus), sensory_profile (what overload), communication_style (what exchange difficulty), recommendation (no_spectrum/mild_flexibility_support/significant_structured_accommodation/major_intensive_support/emergency_complete_rigidity)."""

EPISTEMIC_AUTISM_SPECTRUM_PROMPT = """Detect epistemic autism spectrum:

Rigidity level: {rigidity_level}
Special interest pattern: {special_interest_pattern}
Sensory profile: {sensory_profile}
Communication style: {communication_style}
Domain: {domain}
Context: {context}

Are there rigid intellectual patterns with intense focused interests and flexibility difficulty? Return ONLY valid JSON."""


class EpistemicAutismSpectrumService:
    """Detects epistemic autism spectrum — rigid intellectual patterns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rigidity_level: str,
        *,
        special_interest_pattern: str = "",
        sensory_profile: str = "",
        communication_style: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic autism spectrum."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTISM_SPECTRUM_PROMPT.format(
                rigidity_level=rigidity_level,
                special_interest_pattern=special_interest_pattern or "Not specified",
                sensory_profile=sensory_profile or "Not specified",
                communication_style=communication_style or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTISM_SPECTRUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rigidity_level": rigidity_level[:200],
            "spectrum_detected": data.get("spectrum_detected", False),
            "severity": data.get("severity", ""),
            "special_interest_pattern": data.get("special_interest_pattern", ""),
            "sensory_profile": data.get("sensory_profile", ""),
            "communication_style": data.get("communication_style", ""),
            "recommendation": data.get("recommendation", ""),
        }
