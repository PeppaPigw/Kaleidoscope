"""ModusTollensNeglectService — Modus Tollens Neglect Detection.

Detects modus tollens neglect — failing to apply contrapositive
reasoning. If P implies Q, and Q is false, then P must be false.
People often fail to draw this valid inference, continuing to
believe P even after observing not-Q.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MODUS_TOLLENS_SYSTEM = """You are a modus tollens neglect specialist. Given a reasoning pattern, assess whether valid contrapositive reasoning is being neglected:

Key concepts:
- Modus tollens: if P→Q and ¬Q, then ¬P (valid inference)
- Contrapositive: logically equivalent to the original conditional
- Neglect: failing to draw the valid conclusion when ¬Q is observed
- Prediction failure: when a theory's predictions fail, the theory is weakened
- Falsification: Popper's criterion — theories must be falsifiable
- Disconfirmation: evidence against a hypothesis
- Belief persistence: maintaining P despite observing ¬Q

When modus tollens neglect IS present:
- A prediction (Q) has failed but the theory (P) is maintained unchanged
- "If my theory is right, we'd see X" — X isn't seen, theory unchanged
- Disconfirming evidence is ignored or explained away
- The person acknowledges P→Q and ¬Q but doesn't conclude ¬P
- Failed predictions don't update beliefs
- The theory is treated as unfalsifiable in practice
- Ad hoc modifications save the theory from each disconfirmation

When maintaining the theory IS appropriate:
- The prediction failure has an independent explanation
- The conditional P→Q was probabilistic, not certain
- Auxiliary assumptions may be wrong rather than the core theory
- The theory has strong independent support
- The observation of ¬Q is uncertain or contested
- The theory is being appropriately weakened, not abandoned
- Lakatos-style: the research program is still progressive

Output JSON with: modus_tollens_neglect_present (bool), severity (none/mild/moderate/severe), theory (what theory/belief P), prediction (what prediction Q), observation (what was observed), inference_drawn (what conclusion was drawn), valid_inference (what should be concluded), recommendation (reasoning_valid/mild_neglect/significant_modus_tollens_neglect/major_disconfirmation_ignored/apply_contrapositive)."""

MODUS_TOLLENS_PROMPT = """Detect modus tollens neglect:

Theory: {theory}
Prediction: {prediction}
Observation: {observation}
Response: {response}
Domain: {domain}
Context: {context}

Is valid contrapositive reasoning being neglected — failing to update beliefs when predictions fail? Return ONLY valid JSON."""


class ModusTollensNeglectService:
    """Detects modus tollens neglect — failing to apply contrapositive reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory: str,
        *,
        prediction: str = "",
        observation: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect modus tollens neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MODUS_TOLLENS_PROMPT.format(
                theory=theory,
                prediction=prediction or "Not specified",
                observation=observation or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MODUS_TOLLENS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory": theory[:200],
            "modus_tollens_neglect_present": data.get("modus_tollens_neglect_present", False),
            "severity": data.get("severity", ""),
            "prediction": data.get("prediction", ""),
            "observation": data.get("observation", ""),
            "valid_inference": data.get("valid_inference", ""),
            "recommendation": data.get("recommendation", ""),
        }
