"""EpistemicCoercionService — Epistemic Coercion Detection.

Detects epistemic coercion — forcing belief adoption through
non-epistemic pressure rather than evidence or argument.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COERCION_SYSTEM = """You are an epistemic coercion specialist. Given a belief-formation context, assess whether beliefs are being forced through non-epistemic pressure:

Key concepts:
- Epistemic coercion: forcing beliefs through non-epistemic means
- Belief under duress: adopting beliefs due to threats
- Social pressure on belief: conforming beliefs to social demands
- Professional coercion: beliefs forced by career consequences
- Institutional pressure: institutions forcing belief conformity
- Emotional manipulation: using emotions to force belief
- Consequence-based belief: believing because of consequences not evidence

When epistemic coercion IS present:
- Beliefs forced through threats or consequences
- Non-epistemic pressure driving belief adoption
- Social punishment for holding certain beliefs
- Career consequences for epistemic positions
- Institutional demands for belief conformity
- Emotional manipulation forcing belief change
- Consequences rather than evidence driving belief

When legitimate persuasion is present:
- Beliefs changed through evidence and argument
- Social discussion without coercive pressure
- Professional standards based on evidence
- Institutional norms grounded in knowledge
- Emotional engagement supporting understanding
- Consequences following from truth not conformity

Output JSON with: coercion_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), pressure (what pressure is applied), belief_forced (what belief is forced), mechanism (how coercion operates), recommendation (legitimate_persuasion/mild_pressure/significant_epistemic_coercion/major_belief_forcing/respect_epistemic_freedom)."""

EPISTEMIC_COERCION_PROMPT = """Detect epistemic coercion:

Situation: {situation}
Pressure applied: {pressure}
Belief at stake: {belief}
Consequences: {consequences}
Domain: {domain}
Context: {context}

Are beliefs being forced through non-epistemic pressure? Return ONLY valid JSON."""


class EpistemicCoercionService:
    """Detects epistemic coercion — forcing beliefs through non-epistemic pressure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        pressure: str = "",
        belief: str = "",
        consequences: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic coercion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COERCION_PROMPT.format(
                situation=situation,
                pressure=pressure or "Not specified",
                belief=belief or "Not specified",
                consequences=consequences or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COERCION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "coercion_present": data.get("coercion_present", False),
            "severity": data.get("severity", ""),
            "pressure": data.get("pressure", ""),
            "belief_forced": data.get("belief_forced", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
