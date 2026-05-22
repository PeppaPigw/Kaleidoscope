"""CommitmentConsistencyService — Commitment & Consistency Bias Detection.

Detects commitment and consistency bias — tendency to behave
consistently with prior commitments even when circumstances
have changed. Cialdini (2001). Once people commit to a
position, they feel pressure to behave consistently with it
regardless of new information. Public commitments are
especially binding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMMITMENT_CONSISTENCY_SYSTEM = """You are a commitment and consistency specialist. Given a decision or behavior, assess whether consistency pressure from prior commitments is overriding rational updating:

Key concepts (Cialdini, 2001):
- Commitment and consistency: desire to appear consistent
- Public commitment: public statements are more binding
- Written commitment: written positions harder to abandon
- Cognitive dissonance: discomfort from inconsistency
- Escalation of commitment: doubling down on prior choices
- Sunk cost interaction: past investment reinforcing commitment
- Identity-based commitment: "I'm the kind of person who..."

When commitment/consistency IS problematic:
- Maintaining a position despite new contradicting evidence
- "I already said X, so I have to keep saying X"
- Public statements preventing private belief updating
- Doubling down on failing strategies to appear consistent
- "I've always believed Y" preventing genuine reconsideration
- Fear of being seen as a flip-flopper overriding judgment
- Past commitments constraining current optimal choices

When consistency IS appropriate:
- The original commitment was well-reasoned and still valid
- Consistency reflects genuine stable values
- The person has considered new information and still agrees
- Reliability and predictability serve important functions
- The commitment reflects deep values, not surface positions

Output JSON with: commitment_consistency_present (bool), severity (none/mild/moderate/severe), situation (what decision is being made), prior_commitment (what was previously committed to), new_information (what new information exists), consistency_pressure (what pressure to be consistent exists), public_commitment (was the commitment public), updating_blocked (is belief updating being blocked), recommendation (consistency_appropriate/mild_rigidity/significant_consistency_pressure/major_commitment_trap/evaluate_independently_of_prior_position)."""

COMMITMENT_CONSISTENCY_PROMPT = """Detect commitment and consistency bias:

Situation: {situation}
Prior commitment: {commitment}
New information: {new_info}
Pressure: {pressure}
Domain: {domain}
Context: {context}

Is consistency pressure from prior commitments overriding rational updating? Return ONLY valid JSON."""


class CommitmentConsistencyService:
    """Detects commitment/consistency bias — prior commitments blocking updating."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        commitment: str = "",
        new_info: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect commitment and consistency bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMMITMENT_CONSISTENCY_PROMPT.format(
                situation=situation,
                commitment=commitment or "Not specified",
                new_info=new_info or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMMITMENT_CONSISTENCY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "commitment_consistency_present": data.get("commitment_consistency_present", False),
            "severity": data.get("severity", ""),
            "prior_commitment": data.get("prior_commitment", ""),
            "new_information": data.get("new_information", ""),
            "consistency_pressure": data.get("consistency_pressure", ""),
            "public_commitment": data.get("public_commitment", ""),
            "updating_blocked": data.get("updating_blocked", ""),
            "recommendation": data.get("recommendation", ""),
        }
