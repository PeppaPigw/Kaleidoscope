"""ReificationFallacyService — Reification Fallacy Detection.

Detects the reification fallacy — treating abstract concepts,
models, or categories as if they were concrete, tangible things
with causal power. "The economy wants..." "Intelligence causes..."
"Society demands..." — abstractions don't have agency, desires,
or causal power. They're useful descriptions, not actors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REIFICATION_FALLACY_SYSTEM = """You are a reification fallacy specialist. Given a claim or explanation, assess whether abstract concepts are being treated as concrete entities with causal power:

Key concepts:
- Reification: treating abstractions as concrete things
- Hypostatization: giving abstract concepts independent existence
- Misplaced concreteness: Whitehead's fallacy of treating models as reality
- Category mistake: attributing properties to wrong ontological category
- Anthropomorphization of concepts: "the market wants," "evolution designed"
- Nominal fallacy: naming something doesn't explain it
- Causal attribution to abstractions: abstractions don't cause things

When reification IS present:
- "The economy is punishing us" (economy isn't an agent)
- "Intelligence causes success" (intelligence is a description, not a cause)
- "Society demands conformity" (society isn't a unified agent)
- "Evolution designed this" (evolution has no intentions)
- "The data shows" (data doesn't show, people interpret)
- "Nature intended" (nature has no intentions)
- Treating IQ, GDP, or other metrics as real things rather than measurements

When abstraction IS appropriate:
- Used as shorthand with awareness it's a simplification
- The abstraction is acknowledged as a model, not reality
- Causal claims are about underlying mechanisms, not the abstraction
- The speaker can unpack the abstraction into concrete processes
- Metaphorical language is recognized as metaphor

Output JSON with: reification_present (bool), severity (none/mild/moderate/severe), concept (what abstract concept is being reified), attribution (what properties are being attributed), actual_mechanism (what concrete processes are actually involved), category_error (what category mistake is being made), consequences (how does reification affect reasoning), unpacking (can the abstraction be unpacked into concrete processes), recommendation (abstraction_appropriate/mild_reification/significant_reification_fallacy/major_misplaced_concreteness/unpack_into_concrete_mechanisms)."""

REIFICATION_FALLACY_PROMPT = """Detect reification fallacy:

Claim: {claim}
Concept: {concept}
Attribution: {attribution}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is an abstract concept being treated as a concrete entity with causal power? Return ONLY valid JSON."""


class ReificationFallacyService:
    """Detects reification fallacy — treating abstractions as concrete things."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        concept: str = "",
        attribution: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reification fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REIFICATION_FALLACY_PROMPT.format(
                claim=claim,
                concept=concept or "Not specified",
                attribution=attribution or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REIFICATION_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "reification_present": data.get("reification_present", False),
            "severity": data.get("severity", ""),
            "concept": data.get("concept", ""),
            "attribution": data.get("attribution", ""),
            "actual_mechanism": data.get("actual_mechanism", ""),
            "category_error": data.get("category_error", ""),
            "consequences": data.get("consequences", ""),
            "unpacking": data.get("unpacking", ""),
            "recommendation": data.get("recommendation", ""),
        }
