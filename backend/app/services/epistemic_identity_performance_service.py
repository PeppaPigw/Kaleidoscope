"""EpistemicIdentityPerformanceService — Epistemic Identity Performance Detection.

Detects epistemic identity performance — performing an intellectual
identity rather than genuinely inhabiting it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_PERFORMANCE_SYSTEM = """You are an epistemic identity performance specialist. Given performing intellectual identity, assess identity performance:

Key concepts:
- Epistemic identity performance: performing rather than inhabiting identity
- Intellectual cosplay: dressing up as a type of thinker without being one
- Role playing: playing the role of intellectual without substance
- Identity costume: wearing intellectual identity as costume
- Persona maintenance: maintaining intellectual persona disconnected from self
- Authenticity gap: gap between performed and actual intellectual self
- Image management: managing intellectual image rather than developing thought

When epistemic identity performance IS present:
- Performing rather than inhabiting
- Dressing up as thinker without being
- Playing role without substance
- Wearing identity as costume
- Maintaining disconnected persona
- Gap between performed and actual
- Managing image not developing thought

When no identity performance:
- Genuinely inhabiting identity
- Being the thinker one appears
- Substance behind role
- Identity as genuine expression
- Persona connected to self
- Performed matches actual
- Developing thought genuinely

Output JSON with: identity_performance_detected (bool), severity (none/mild/moderate/severe), intellectual_cosplay (what dressing up as without being), role_playing (what playing role without substance), authenticity_gap (what gap between performed and actual), image_management (what managing image of), recommendation (no_identity_performance/mild_authenticity_check/significant_genuine_inhabiting/major_intensive_identity_alignment/emergency_complete_identity_fabrication)."""

EPISTEMIC_IDENTITY_PERFORMANCE_PROMPT = """Detect epistemic identity performance:

Intellectual cosplay: {intellectual_cosplay}
Role playing: {role_playing}
Authenticity gap: {authenticity_gap}
Image management: {image_management}
Domain: {domain}
Context: {context}

Is there performing an intellectual identity rather than genuinely inhabiting it? Return ONLY valid JSON."""


class EpistemicIdentityPerformanceService:
    """Detects epistemic identity performance — performing rather than inhabiting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        intellectual_cosplay: str,
        *,
        role_playing: str = "",
        authenticity_gap: str = "",
        image_management: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic identity performance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_PERFORMANCE_PROMPT.format(
                intellectual_cosplay=intellectual_cosplay,
                role_playing=role_playing or "Not specified",
                authenticity_gap=authenticity_gap or "Not specified",
                image_management=image_management or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_PERFORMANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "intellectual_cosplay": intellectual_cosplay[:200],
            "identity_performance_detected": data.get("identity_performance_detected", False),
            "severity": data.get("severity", ""),
            "role_playing": data.get("role_playing", ""),
            "authenticity_gap": data.get("authenticity_gap", ""),
            "image_management": data.get("image_management", ""),
            "recommendation": data.get("recommendation", ""),
        }
