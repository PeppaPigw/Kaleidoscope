"""MindProjectionFallacyService — Mind Projection Fallacy Detection.

Detects the mind projection fallacy — projecting properties of
one's own mind onto the external world. Jaynes (2003). Confusing
"I don't know X" with "X is unknowable," or "I find X beautiful"
with "X is beautiful." Treating subjective states as objective
properties of reality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MIND_PROJECTION_SYSTEM = """You are a mind projection fallacy specialist. Given a claim about reality, assess whether subjective mental states are being projected as objective properties:

Key concepts (Jaynes, 2003):
- Mind projection fallacy: projecting mental properties onto the world
- Subjective-objective confusion: treating feelings as facts about reality
- Epistemic-ontic confusion: "I don't know" → "it's unknowable"
- Aesthetic projection: "I find it beautiful" → "it IS beautiful"
- Probability projection: "I'm uncertain" → "it's random"
- Value projection: "I value X" → "X is valuable"
- Complexity projection: "I can't understand it" → "it's incomprehensible"

When mind projection IS present:
- "That's boring" (projecting boredom onto the object)
- "It's unknowable" when meaning "I don't know"
- "That's random" when meaning "I can't predict it"
- "It's obvious" (projecting ease of understanding)
- "That's ugly/beautiful" stated as objective fact
- "It's meaningless" when meaning "I don't see meaning"
- Treating personal taste as universal truth

When objective claims ARE appropriate:
- The claim is about measurable, intersubjective properties
- Subjective framing is acknowledged ("I find it...")
- The claim can be verified independently of the observer
- Aesthetic/value claims are presented as perspectives
- Epistemic limitations are distinguished from ontic properties

Output JSON with: mind_projection_present (bool), severity (none/mild/moderate/severe), claim (what is being claimed about reality), subjective_source (what mental state is being projected), objective_framing (how is it framed as objective), actual_status (is this subjective or objective), verifiability (can this be verified independently), consequences (how does projection affect reasoning), recommendation (claim_objective/mild_projection/significant_mind_projection/major_subjective_as_objective/distinguish_subjective_from_objective)."""

MIND_PROJECTION_PROMPT = """Detect mind projection fallacy:

Claim: {claim}
Framing: {framing}
Subjective element: {subjective}
Objective basis: {objective}
Domain: {domain}
Context: {context}

Are subjective mental states being projected as objective properties of reality? Return ONLY valid JSON."""


class MindProjectionFallacyService:
    """Detects mind projection fallacy — projecting mental states onto reality."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        framing: str = "",
        subjective: str = "",
        objective: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect mind projection fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MIND_PROJECTION_PROMPT.format(
                claim=claim,
                framing=framing or "Not specified",
                subjective=subjective or "Not specified",
                objective=objective or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MIND_PROJECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "mind_projection_present": data.get("mind_projection_present", False),
            "severity": data.get("severity", ""),
            "subjective_source": data.get("subjective_source", ""),
            "objective_framing": data.get("objective_framing", ""),
            "actual_status": data.get("actual_status", ""),
            "verifiability": data.get("verifiability", ""),
            "consequences": data.get("consequences", ""),
            "recommendation": data.get("recommendation", ""),
        }
