"""ConformityCascadeService — Conformity Cascade Detection.

Detects conformity cascades — situations where each person conforms
because others have conformed, creating a chain of agreement that
has no independent epistemic foundation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONFORMITY_CASCADE_SYSTEM = """You are a conformity cascade specialist. Given a group agreement, assess whether conformity is cascading without independent basis:

Key concepts:
- Conformity cascade: each conforms because others did
- Information cascade: following others rather than own evidence
- Herding behavior: following the crowd epistemically
- Independent judgment loss: no one checking independently
- Cascade fragility: agreement based on thin foundation
- Social proof chain: each link is just social proof
- Hollow consensus: agreement without independent verification

When conformity cascade IS present:
- Each person agrees because others agreed
- No independent verification at any point
- Agreement cascades without epistemic foundation
- Social proof substitutes for evidence
- Herding behavior drives consensus
- Independent judgment abandoned
- Consensus fragile because based on cascade

When genuine convergence is present:
- Multiple independent lines of evidence
- Agreement based on shared evidence not social proof
- Independent verification at multiple points
- Convergence robust to individual defection
- Evidence base independent of social dynamics
- Agreement would survive if cascade reversed
- Multiple paths to same conclusion

Output JSON with: cascade_present (bool), severity (none/mild/moderate/severe), situation (what situation is analyzed), cascade_mechanism (how conformity cascades), independent_basis (what independent evidence exists), fragility (how fragile the consensus is), recommendation (genuine_convergence/mild_social_influence/significant_conformity_cascade/major_hollow_consensus/establish_independent_verification)."""

CONFORMITY_CASCADE_PROMPT = """Detect conformity cascade:

Situation: {situation}
Agreement pattern: {pattern}
Independent evidence: {evidence}
Social dynamics: {dynamics}
Domain: {domain}
Context: {context}

Is agreement cascading through conformity rather than independent evidence? Return ONLY valid JSON."""


class ConformityCascadeService:
    """Detects conformity cascades — agreement cascading without independent basis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        pattern: str = "",
        evidence: str = "",
        dynamics: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect conformity cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONFORMITY_CASCADE_PROMPT.format(
                situation=situation,
                pattern=pattern or "Not specified",
                evidence=evidence or "Not specified",
                dynamics=dynamics or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONFORMITY_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "cascade_present": data.get("cascade_present", False),
            "severity": data.get("severity", ""),
            "cascade_mechanism": data.get("cascade_mechanism", ""),
            "independent_basis": data.get("independent_basis", ""),
            "fragility": data.get("fragility", ""),
            "recommendation": data.get("recommendation", ""),
        }
