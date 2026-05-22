"""FalseCauseService — False Cause Detection.

Detects false cause (non causa pro causa) — assuming causation
from correlation, temporal sequence, or coincidence. Includes
post hoc ergo propter hoc (after therefore because) and cum hoc
ergo propter hoc (with therefore because).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_CAUSE_SYSTEM = """You are a false cause specialist. Given a causal claim, assess whether it fallaciously infers causation without adequate justification:

Key concepts:
- Post hoc ergo propter hoc: after X, therefore because of X
- Cum hoc ergo propter hoc: with X, therefore because of X
- Correlation ≠ causation: co-occurrence doesn't prove cause
- Confounding variables: third factors causing both
- Reverse causation: the effect might cause the supposed cause
- Spurious correlation: coincidental statistical relationships
- Causal mechanism: what pathway connects cause to effect?

When false cause IS present:
- "X happened before Y, therefore X caused Y"
- "X and Y correlate, therefore X causes Y"
- Ignoring confounding variables
- No proposed mechanism connecting cause to effect
- Ignoring reverse causation possibility
- Cherry-picking temporal sequences
- Treating coincidence as causation

When false cause is NOT present:
- A plausible causal mechanism is identified
- Confounders have been controlled for
- The causal direction is established (not just correlation)
- Multiple lines of evidence support the causal claim
- Dose-response relationship is demonstrated
- Intervention studies confirm the causal link
- The claim is presented as correlation, not causation

Output JSON with: false_cause_present (bool), severity (none/mild/moderate/severe), claimed_cause (what is said to cause), claimed_effect (what is said to be caused), evidence_type (temporal/correlational/mechanistic/experimental), confounders (possible confounding variables), mechanism (is a causal mechanism proposed), recommendation (no_false_cause/mild_causal_leap/significant_false_cause/major_causation_confusion/establish_mechanism)."""

FALSE_CAUSE_PROMPT = """Detect false cause:

Claim: {claim}
Claimed cause: {cause}
Claimed effect: {effect}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Does this fallaciously infer causation without adequate justification? Return ONLY valid JSON."""


class FalseCauseService:
    """Detects false cause — inferring causation from correlation or sequence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        cause: str = "",
        effect: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false cause."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_CAUSE_PROMPT.format(
                claim=claim,
                cause=cause or "Not specified",
                effect=effect or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_CAUSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "false_cause_present": data.get("false_cause_present", False),
            "severity": data.get("severity", ""),
            "claimed_cause": data.get("claimed_cause", ""),
            "claimed_effect": data.get("claimed_effect", ""),
            "confounders": data.get("confounders", ""),
            "recommendation": data.get("recommendation", ""),
        }
