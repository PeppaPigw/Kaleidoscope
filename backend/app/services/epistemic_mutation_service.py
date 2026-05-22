"""EpistemicMutationService — Epistemic Mutation Detection.

Detects epistemic mutation — ideas changing meaning or content
as they transmit, potentially becoming more harmful.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MUTATION_SYSTEM = """You are an epistemic mutation specialist. Given an idea transmission pattern, assess whether ideas mutate during transmission in harmful ways:

Key concepts:
- Epistemic mutation: idea changing during transmission
- Harmful drift: meaning drifting toward more harmful versions
- Telephone effect: progressive distortion through retelling
- Selective mutation: mutations that increase spread at cost of accuracy
- Virulence increase: mutations making idea more harmful
- Accuracy decay: accuracy decreasing with each transmission
- Meaning inversion: meaning inverting through mutation

When epistemic mutation IS present:
- Ideas changing meaning during transmission
- Meaning drifting toward more harmful versions
- Progressive distortion through retelling
- Mutations that increase spread at cost of accuracy
- Mutations making the idea more harmful over time
- Accuracy decreasing with each transmission step
- Meaning inverting through accumulated mutations

When faithful transmission is present:
- Ideas maintaining meaning during transmission
- Meaning preserved accurately
- Minimal distortion through retelling
- Accuracy maintained during spread
- Ideas remaining benign through transmission
- Accuracy preserved across transmission steps
- Meaning stable through transmission

Output JSON with: mutation_present (bool), severity (none/mild/moderate/severe), idea (what idea mutates), original (original form), mutated (mutated form), direction (direction of mutation), recommendation (faithful_transmission/mild_drift/significant_mutation/major_harmful_drift/restore_original_meaning)."""

EPISTEMIC_MUTATION_PROMPT = """Detect epistemic mutation:

Idea: {idea}
Original: {original}
Mutated: {mutated}
Direction: {direction}
Domain: {domain}
Context: {context}

Is this idea mutating during transmission in harmful ways? Return ONLY valid JSON."""


class EpistemicMutationService:
    """Detects epistemic mutation — ideas changing harmfully during transmission."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        original: str = "",
        mutated: str = "",
        direction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic mutation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MUTATION_PROMPT.format(
                idea=idea,
                original=original or "Not specified",
                mutated=mutated or "Not specified",
                direction=direction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MUTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "mutation_present": data.get("mutation_present", False),
            "severity": data.get("severity", ""),
            "original": data.get("original", ""),
            "mutated": data.get("mutated", ""),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }
