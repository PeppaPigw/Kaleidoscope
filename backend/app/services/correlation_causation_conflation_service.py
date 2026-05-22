"""CorrelationCausationConflationService — Correlation-Causation Conflation Detection.

Detects when correlation is treated as proof of causation
without adequate evidence for a causal mechanism, temporal
precedence, or elimination of confounders.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CORRELATION_CAUSATION_SYSTEM = """You are a correlation-causation conflation specialist. Given a causal claim, assess whether correlation is being treated as causation:

Key concepts:
- Correlation vs causation: co-occurrence doesn't prove cause
- Confounders: third variables explaining both
- Reverse causation: effect causing the supposed cause
- Temporal precedence: cause must precede effect
- Mechanism: plausible pathway from cause to effect
- Dose-response: stronger cause = stronger effect
- Hill's criteria: guidelines for inferring causation

When conflation IS present:
- Correlation presented as proof of causation
- No confounders considered or controlled for
- Reverse causation not ruled out
- No mechanism proposed for the causal link
- "X is associated with Y, therefore X causes Y"
- Observational data treated as experimental
- Third variable explanations not considered

When causation is properly established:
- Confounders identified and controlled
- Temporal precedence established
- Plausible mechanism proposed
- Dose-response relationship shown
- Reverse causation ruled out
- Experimental or quasi-experimental evidence
- Alternative explanations systematically eliminated

Output JSON with: conflation_present (bool), severity (none/mild/moderate/severe), claimed_cause (what is said to cause), claimed_effect (what is said to be caused), evidence_type (correlational/experimental/quasi-experimental), confounders (potential third variables), mechanism (proposed causal pathway), recommendation (causation_established/mild_overstatement/significant_conflation/major_correlation_as_causation/establish_mechanism)."""

CORRELATION_CAUSATION_PROMPT = """Detect correlation-causation conflation:

Claim: {claim}
Evidence: {evidence}
Confounders: {confounders}
Mechanism: {mechanism}
Domain: {domain}
Context: {context}

Is correlation being treated as proof of causation? Return ONLY valid JSON."""


class CorrelationCausationConflationService:
    """Detects correlation-causation conflation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        confounders: str = "",
        mechanism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect correlation-causation conflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CORRELATION_CAUSATION_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                confounders=confounders or "Not specified",
                mechanism=mechanism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CORRELATION_CAUSATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "conflation_present": data.get("conflation_present", False),
            "severity": data.get("severity", ""),
            "evidence_type": data.get("evidence_type", ""),
            "confounders": data.get("confounders", ""),
            "mechanism": data.get("mechanism", ""),
            "recommendation": data.get("recommendation", ""),
        }
