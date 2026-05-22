"""CommitmentDeviceService — Commitment Device Assessment.

Assesses whether commitment devices are appropriate — pre-
commitment strategies that restrict future choices to overcome
present bias. Evaluates whether the device is well-designed
or potentially harmful.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMMITMENT_DEVICE_SYSTEM = """You are a commitment device specialist. Given a pre-commitment strategy, assess whether it is appropriate and well-designed:

Key concepts:
- Commitment device: restricting future choices to overcome present bias
- Ulysses contract: binding oneself against future temptation
- Present bias: overweighting immediate over future preferences
- Flexibility vs commitment: tradeoff between options and discipline
- Escape clauses: ability to exit if circumstances change
- Proportionality: commitment matched to the problem
- Autonomy: respecting future self's legitimate preferences

When commitment device IS appropriate:
- Clear present bias that the device addresses
- Future self would endorse the commitment
- Proportional to the problem being solved
- Escape clause for genuinely changed circumstances
- Reversible if the goal changes
- Addresses a specific, identified weakness
- Benefits outweigh loss of flexibility

When commitment device is problematic:
- Restricts legitimate future choices
- Disproportionate to the problem
- No escape clause for changed circumstances
- Future self might have legitimate reasons to deviate
- Commitment based on current preferences that may change
- Inflexible in the face of new information
- Paternalistic toward future self without justification

Output JSON with: appropriate (bool), assessment (well_designed/over_committed/under_committed/harmful), problem_addressed (what present bias it targets), flexibility_cost (what options are lost), escape_clause (whether exit is possible), proportionality (whether commitment matches problem), recommendation (well_designed/add_escape_clause/reduce_commitment/increase_commitment/reconsider_approach)."""

COMMITMENT_DEVICE_PROMPT = """Assess commitment device:

Strategy: {strategy}
Goal: {goal}
Restrictions: {restrictions}
Flexibility: {flexibility}
Domain: {domain}
Context: {context}

Is this commitment device appropriate and well-designed? Return ONLY valid JSON."""


class CommitmentDeviceService:
    """Assesses commitment devices — pre-commitment strategy evaluation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        strategy: str,
        *,
        goal: str = "",
        restrictions: str = "",
        flexibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess commitment device."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMMITMENT_DEVICE_PROMPT.format(
                strategy=strategy,
                goal=goal or "Not specified",
                restrictions=restrictions or "Not specified",
                flexibility=flexibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMMITMENT_DEVICE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategy": strategy[:200],
            "appropriate": data.get("appropriate", False),
            "assessment": data.get("assessment", ""),
            "flexibility_cost": data.get("flexibility_cost", ""),
            "escape_clause": data.get("escape_clause", ""),
            "proportionality": data.get("proportionality", ""),
            "recommendation": data.get("recommendation", ""),
        }
