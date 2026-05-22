"""SocialProofCascadeService — Social Proof Cascade Detection.

Detects social proof cascade — when people follow others'
behavior in sequence, creating a self-reinforcing cascade
where later actors have increasingly distorted information.
Banerjee (1992), Bikhchandani, Hirshleifer & Welch (1992).
"Everyone else is doing it" becomes the reason, regardless
of private information suggesting otherwise.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SOCIAL_PROOF_CASCADE_SYSTEM = """You are a social proof cascade specialist. Given a decision influenced by others' behavior, assess whether a cascade is forming where private information is being overridden by observed behavior:

Key concepts (Banerjee, 1992; Bikhchandani et al., 1992):
- Informational cascade: following others overrides private signal
- Social proof: others' behavior as evidence of correctness
- Herding: following the crowd regardless of private information
- Cascade fragility: cascades can be wrong and break suddenly
- Rational herding: sometimes rational to follow others
- Irrational exuberance: cascades in financial markets
- Conformity pressure: social cost of going against the crowd

When social proof cascade IS present:
- Following others' choices while ignoring own information
- "Everyone else is buying/doing it, so it must be right"
- Sequential decisions where later actors copy earlier ones
- Private doubts suppressed because of observed consensus
- Trends that grow through imitation rather than independent evaluation
- "The market can't be wrong" despite contradicting evidence
- Adoption driven by popularity rather than quality assessment

When following others IS rational:
- Others genuinely have better information
- The person has weak private signals
- Network effects make popular choices genuinely better
- The cost of independent evaluation exceeds the benefit
- Others' behavior reveals genuine quality information

Output JSON with: social_proof_cascade_present (bool), severity (none/mild/moderate/severe), situation (what decision is being influenced), cascade_evidence (what social proof is being followed), private_information (what private information is being overridden), cascade_size (how many have already followed), fragility (how fragile is the cascade), independent_evaluation (has independent evaluation been done), recommendation (following_rational/mild_herding/significant_cascade/major_social_proof_override/evaluate_independently)."""

SOCIAL_PROOF_CASCADE_PROMPT = """Detect social proof cascade:

Situation: {situation}
Others' behavior: {others}
Own information: {own_info}
Pressure: {pressure}
Domain: {domain}
Context: {context}

Is social proof creating a cascade that overrides private information? Return ONLY valid JSON."""


class SocialProofCascadeService:
    """Detects social proof cascade — following others overriding private information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        others: str = "",
        own_info: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect social proof cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SOCIAL_PROOF_CASCADE_PROMPT.format(
                situation=situation,
                others=others or "Not specified",
                own_info=own_info or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SOCIAL_PROOF_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "social_proof_cascade_present": data.get("social_proof_cascade_present", False),
            "severity": data.get("severity", ""),
            "cascade_evidence": data.get("cascade_evidence", ""),
            "private_information": data.get("private_information", ""),
            "cascade_size": data.get("cascade_size", ""),
            "fragility": data.get("fragility", ""),
            "independent_evaluation": data.get("independent_evaluation", ""),
            "recommendation": data.get("recommendation", ""),
        }
