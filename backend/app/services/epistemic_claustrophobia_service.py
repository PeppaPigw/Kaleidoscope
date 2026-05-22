"""EpistemicClaustrophobiaService — Epistemic Claustrophobia Detection.

Detects epistemic claustrophobia — fear of narrow intellectual constraints
and feeling trapped within rigid frameworks or paradigms.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CLAUSTROPHOBIA_SYSTEM = """You are an epistemic claustrophobia specialist. Given fear of intellectual constraints, assess claustrophobia:

Key concepts:
- Epistemic claustrophobia: fear of narrow intellectual constraints
- Confinement: feeling trapped within rigid frameworks
- Suffocation: intellectual breathing restricted by paradigm
- Panic: overwhelming need to break free from constraints
- Escape urge: desperate need to abandon current framework
- Restriction sensitivity: extreme discomfort with boundaries
- Expansive need: requiring intellectual freedom to function

When epistemic claustrophobia IS present:
- Fear of narrow constraints
- Feeling trapped in frameworks
- Intellectual breathing restricted
- Overwhelming need to break free
- Desperate to abandon framework
- Extreme discomfort with boundaries
- Requiring freedom to function

When no claustrophobia:
- Comfortable with constraints
- Frameworks feel supportive
- Intellectual breathing easy
- Calm within structure
- Content with framework
- Comfortable with boundaries
- Functioning within structure

Output JSON with: claustrophobia_detected (bool), severity (none/mild/moderate/severe), confinement_trigger (what constraints), suffocation_level (what restriction), escape_urgency (what break-free need), restriction_tolerance (what boundary comfort), recommendation (no_claustrophobia/mild_boundary_flexibility/significant_framework_expansion/major_intensive_liberation/emergency_complete_panic)."""

EPISTEMIC_CLAUSTROPHOBIA_PROMPT = """Detect epistemic claustrophobia:

Confinement trigger: {confinement_trigger}
Suffocation level: {suffocation_level}
Escape urgency: {escape_urgency}
Restriction tolerance: {restriction_tolerance}
Domain: {domain}
Context: {context}

Is there fear of narrow intellectual constraints with feeling trapped in rigid frameworks? Return ONLY valid JSON."""


class EpistemicClaustrophobiaService:
    """Detects epistemic claustrophobia — fear of intellectual constraints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        confinement_trigger: str,
        *,
        suffocation_level: str = "",
        escape_urgency: str = "",
        restriction_tolerance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic claustrophobia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CLAUSTROPHOBIA_PROMPT.format(
                confinement_trigger=confinement_trigger,
                suffocation_level=suffocation_level or "Not specified",
                escape_urgency=escape_urgency or "Not specified",
                restriction_tolerance=restriction_tolerance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CLAUSTROPHOBIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "confinement_trigger": confinement_trigger[:200],
            "claustrophobia_detected": data.get("claustrophobia_detected", False),
            "severity": data.get("severity", ""),
            "suffocation_level": data.get("suffocation_level", ""),
            "escape_urgency": data.get("escape_urgency", ""),
            "restriction_tolerance": data.get("restriction_tolerance", ""),
            "recommendation": data.get("recommendation", ""),
        }
