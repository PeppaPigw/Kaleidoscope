"""NotEvenWrongService — Not Even Wrong Detection.

Detects 'not even wrong' claims — statements so vague, unfalsifiable,
or disconnected from empirical reality that they cannot even be
evaluated as true or false. Wolfgang Pauli. A claim that is "not
even wrong" fails to make contact with reality in a way that would
allow testing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NOT_EVEN_WRONG_SYSTEM = """You are a 'not even wrong' specialist. Given a claim or theory, assess whether it is so vague or unfalsifiable that it cannot be evaluated:

Key concepts (Pauli):
- Not even wrong: too vague to be testable
- Unfalsifiability: no possible observation could disprove it
- Empirical disconnection: no contact with observable reality
- Pseudo-explanation: appears to explain but predicts nothing
- Vacuous truth: true by virtue of saying nothing
- Moving target: claim shifts to avoid any possible refutation
- Semantic emptiness: words without operational meaning

When 'not even wrong' IS present:
- Claims that cannot be tested even in principle
- Theories that explain everything (and therefore nothing)
- Statements so vague they're compatible with any observation
- "Explanations" that make no predictions
- Claims that shift meaning when challenged
- Frameworks that cannot specify what would disprove them
- Technical-sounding language with no operational definitions

When vagueness IS appropriate:
- Early-stage hypothesis that will be refined
- Explicitly acknowledged as speculative or directional
- The vagueness is in presentation, not in the underlying model
- Operational definitions are available but omitted for brevity
- The claim is explicitly unfalsifiable by design (values, aesthetics)
- It's a heuristic or rule of thumb, not a truth claim
- The domain genuinely resists precise formulation at this stage

Output JSON with: not_even_wrong_present (bool), severity (none/mild/moderate/severe), claim (the claim analyzed), falsifiability (could any observation disprove it), predictions (what does it predict), operational_definitions (are key terms defined operationally), vagueness_source (where does the vagueness come from), recommendation (appropriately_vague/mild_imprecision/significant_unfalsifiability/major_empirical_disconnection/operationalize_claims)."""

NOT_EVEN_WRONG_PROMPT = """Detect 'not even wrong':

Claim: {claim}
Predictions: {predictions}
Falsification: {falsification}
Definitions: {definitions}
Domain: {domain}
Context: {context}

Is this claim so vague or unfalsifiable that it cannot even be evaluated as true or false? Return ONLY valid JSON."""


class NotEvenWrongService:
    """Detects 'not even wrong' claims — unfalsifiable vagueness."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        predictions: str = "",
        falsification: str = "",
        definitions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect 'not even wrong' claims."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NOT_EVEN_WRONG_PROMPT.format(
                claim=claim,
                predictions=predictions or "Not specified",
                falsification=falsification or "Not specified",
                definitions=definitions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NOT_EVEN_WRONG_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "not_even_wrong_present": data.get("not_even_wrong_present", False),
            "severity": data.get("severity", ""),
            "falsifiability": data.get("falsifiability", ""),
            "predictions": data.get("predictions", ""),
            "operational_definitions": data.get("operational_definitions", ""),
            "vagueness_source": data.get("vagueness_source", ""),
            "recommendation": data.get("recommendation", ""),
        }
