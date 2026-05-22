"""EpistemicMultiverseService — Epistemic Multiverse Detection.

Detects epistemic multiverse — parallel intellectual universes with different
axioms coexisting, each internally consistent but mutually incompatible.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MULTIVERSE_SYSTEM = """You are an epistemic multiverse specialist. Given an intellectual landscape, assess whether parallel universes with different axioms coexist:

Key concepts:
- Epistemic multiverse: parallel intellectual universes with different axioms
- Many worlds: every decision branching into separate universes
- Landscape: vast space of possible consistent frameworks
- Bubble universe: isolated region with its own laws
- Decoherence: branches losing ability to interfere
- Anthropic selection: we observe our universe because we exist in it
- Level classification: different types of parallel existence

When epistemic multiverse IS present:
- Parallel intellectual universes with different axioms coexisting
- Every decision branching into separate intellectual worlds
- Vast space of possible consistent frameworks
- Isolated regions with their own intellectual laws
- Branches losing ability to communicate
- Selection effects explaining why we see what we see
- Multiple levels of parallel existence

When single universe is present:
- Only one intellectual framework
- No branching at decisions
- Single consistent framework
- No isolated regions
- Full communication between all parts
- No selection effects needed
- Single level of existence

Output JSON with: multiverse_present (bool), severity (none/mild/moderate/severe), many_worlds (what branching), landscape (what framework space), bubble_universe (what isolated region), decoherence (what communication loss), recommendation (single_universe/mild_multiverse/significant_multiverse/major_parallel_existence/bridge_between_universes)."""

EPISTEMIC_MULTIVERSE_PROMPT = """Detect epistemic multiverse:

Many worlds: {many_worlds}
Landscape: {landscape}
Bubble universe: {bubble_universe}
Decoherence: {decoherence}
Domain: {domain}
Context: {context}

Are parallel intellectual universes with different axioms coexisting, each internally consistent but mutually incompatible? Return ONLY valid JSON."""


class EpistemicMultiverseService:
    """Detects epistemic multiverse — parallel intellectual universes with different axioms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        many_worlds: str,
        *,
        landscape: str = "",
        bubble_universe: str = "",
        decoherence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic multiverse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MULTIVERSE_PROMPT.format(
                many_worlds=many_worlds,
                landscape=landscape or "Not specified",
                bubble_universe=bubble_universe or "Not specified",
                decoherence=decoherence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MULTIVERSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "many_worlds": many_worlds[:200],
            "multiverse_present": data.get("multiverse_present", False),
            "severity": data.get("severity", ""),
            "landscape": data.get("landscape", ""),
            "bubble_universe": data.get("bubble_universe", ""),
            "decoherence": data.get("decoherence", ""),
            "recommendation": data.get("recommendation", ""),
        }
