"""ScopeNeglectService — Scope Neglect Detection.

Detects scope neglect — insensitivity to the magnitude or
scope of a problem when making judgments. Desvousges et al.
(1993), Kahneman (1986). People are willing to pay roughly
the same to save 2,000, 20,000, or 200,000 birds. The
emotional response doesn't scale with the numbers.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_NEGLECT_SYSTEM = """You are a scope neglect specialist. Given a judgment or valuation, assess whether the response is appropriately sensitive to the magnitude of the problem:

Key concepts (Desvousges et al., 1993; Kahneman, 1986):
- Scope neglect: insensitivity to magnitude/scale
- Scope insensitivity: valuation doesn't scale with quantity
- Prototype heuristic: evaluating a representative instance, not the whole
- Affect heuristic interaction: emotional response doesn't scale
- Psychophysical numbing: large numbers lose emotional impact
- Embedding effect: valuation of part ≈ valuation of whole
- Extension neglect: ignoring how many instances are affected

When scope neglect IS present:
- Willingness to pay/act doesn't scale with problem magnitude
- Same emotional response to 10 vs 10,000 affected
- "That's terrible" regardless of whether it's 1 or 1 million
- Resource allocation insensitive to scale of impact
- Treating a small problem with same urgency as a large one
- Donations/effort that don't reflect relative magnitudes
- "A tragedy is a tragedy" regardless of scope

When the response IS scope-appropriate:
- Valuation scales proportionally with magnitude
- The person explicitly considers and responds to scale
- Resource allocation reflects relative magnitudes
- There are genuine reasons for non-linear response (diminishing returns)
- The person distinguishes between different scales of impact

Output JSON with: scope_neglect_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), scope (what is the actual magnitude), response (what is the response/valuation), scaling (does response scale with magnitude?), prototype_used (is a single instance being evaluated?), magnitude_acknowledged (is the full scope acknowledged?), proportional_response (what would a proportional response look like?), recommendation (response_appropriate/mild_scope_neglect/significant_insensitivity/major_scope_neglect/scale_response_to_magnitude)."""

SCOPE_NEGLECT_PROMPT = """Detect scope neglect:

Judgment: {judgment}
Magnitude: {magnitude}
Response: {response}
Comparison: {comparison}
Domain: {domain}
Context: {context}

Is the response appropriately sensitive to the magnitude of the problem? Return ONLY valid JSON."""


class ScopeNeglectService:
    """Detects scope neglect — insensitivity to magnitude when making judgments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        magnitude: str = "",
        response: str = "",
        comparison: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scope neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_NEGLECT_PROMPT.format(
                judgment=judgment,
                magnitude=magnitude or "Not specified",
                response=response or "Not specified",
                comparison=comparison or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCOPE_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "scope_neglect_present": data.get("scope_neglect_present", False),
            "severity": data.get("severity", ""),
            "scope": data.get("scope", ""),
            "scaling": data.get("scaling", ""),
            "prototype_used": data.get("prototype_used", ""),
            "magnitude_acknowledged": data.get("magnitude_acknowledged", ""),
            "proportional_response": data.get("proportional_response", ""),
            "recommendation": data.get("recommendation", ""),
        }
