"""EpistemicWeakForceService — Epistemic Weak Force Detection.

Detects epistemic weak force — a subtle intellectual force that changes
the fundamental nature of ideas, transforming one type into another.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WEAK_FORCE_SYSTEM = """You are an epistemic weak force specialist. Given an intellectual transformation, assess whether a subtle force is changing the nature of ideas:

Key concepts:
- Epistemic weak force: subtle force changing the nature of ideas
- Flavor change: transforming one type of idea into another
- W boson: carrier of the type-changing force
- Z boson: carrier of neutral current interaction
- Parity violation: force distinguishing left from right
- Beta decay: slow transformation of one type to another
- Cabibbo angle: mixing between generations

When epistemic weak force IS present:
- Subtle force changing the fundamental nature of ideas
- One type of idea transforming into another
- Specific carrier mediating the transformation
- Neutral interactions that don't change type
- Force distinguishing between orientations
- Slow transformation processes
- Mixing between different generations of ideas

When type-preserving force is present:
- No force changing idea nature
- Ideas maintaining their type
- No transformation carriers
- All interactions preserving type
- No orientation preference
- No slow transformations
- No generational mixing

Output JSON with: weak_force_present (bool), severity (none/mild/moderate/severe), flavor_change (what type transformation), w_boson (what transformation carrier), parity_violation (what orientation preference), beta_decay (what slow transformation), recommendation (type_preserving/mild_weak_force/significant_weak_force/major_type_change/identify_transformation_carrier)."""

EPISTEMIC_WEAK_FORCE_PROMPT = """Detect epistemic weak force:

Flavor change: {flavor_change}
W boson: {w_boson}
Parity violation: {parity_violation}
Beta decay: {beta_decay}
Domain: {domain}
Context: {context}

Is a subtle intellectual force changing the fundamental nature of ideas, transforming one type into another? Return ONLY valid JSON."""


class EpistemicWeakForceService:
    """Detects epistemic weak force — subtle force changing the nature of ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        flavor_change: str,
        *,
        w_boson: str = "",
        parity_violation: str = "",
        beta_decay: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic weak force."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WEAK_FORCE_PROMPT.format(
                flavor_change=flavor_change,
                w_boson=w_boson or "Not specified",
                parity_violation=parity_violation or "Not specified",
                beta_decay=beta_decay or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WEAK_FORCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "flavor_change": flavor_change[:200],
            "weak_force_present": data.get("weak_force_present", False),
            "severity": data.get("severity", ""),
            "w_boson": data.get("w_boson", ""),
            "parity_violation": data.get("parity_violation", ""),
            "beta_decay": data.get("beta_decay", ""),
            "recommendation": data.get("recommendation", ""),
        }
