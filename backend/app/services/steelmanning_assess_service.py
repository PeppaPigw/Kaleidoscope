"""SteelmanningAssessService — Steelmanning Assessment.

Assesses whether the strongest version of an opposing argument
has been addressed. Steelmanning is the opposite of strawmanning —
it means presenting the best possible version of an argument
before attempting to refute it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STEELMANNING_SYSTEM = """You are a steelmanning assessment specialist. Given a rebuttal or critique, evaluate whether it addresses the strongest version of the opposing argument:

Key concepts:
- Steelmanning: presenting the strongest version of an opposing argument
- Principle of charity: interpreting arguments in their best light
- Strongest version: the version most likely to be correct
- Intellectual honesty: engaging with the best, not worst, opposition
- Weak man vs steel man: attacking weak vs strong versions
- Ideological Turing test: can you state the opposition's view convincingly?
- Productive disagreement: engaging with the strongest opposition

Assessment criteria:
- Does the rebuttal address the strongest version of the argument?
- Are the opponent's best points acknowledged?
- Would the opponent recognize their position in the characterization?
- Are the strongest objections to one's own position considered?
- Is the argument being engaged with charitably?
- Are qualifications and nuances preserved?
- Would addressing this version be more productive?

Output JSON with: steelmanning_quality (poor/fair/good/excellent), strongest_version (what the strongest version would be), version_addressed (what version was actually addressed), gap (difference between strongest and addressed), opponent_recognition (would opponent recognize their view), improvements (how to better steelman), recommendation (excellent_steelmanning/good_engagement/needs_stronger_version/significant_weakening/address_strongest_form)."""

STEELMANNING_PROMPT = """Assess steelmanning quality:

Rebuttal: {rebuttal}
Opposing position: {opposing_position}
Version addressed: {version_addressed}
Strongest version: {strongest_version}
Domain: {domain}
Context: {context}

Does this address the strongest version of the opposing argument? Return ONLY valid JSON."""


class SteelmanningAssessService:
    """Assesses whether the strongest opposing argument is addressed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        rebuttal: str,
        *,
        opposing_position: str = "",
        version_addressed: str = "",
        strongest_version: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess steelmanning quality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STEELMANNING_PROMPT.format(
                rebuttal=rebuttal,
                opposing_position=opposing_position or "Not specified",
                version_addressed=version_addressed or "Not specified",
                strongest_version=strongest_version or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STEELMANNING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rebuttal": rebuttal[:200],
            "steelmanning_quality": data.get("steelmanning_quality", ""),
            "strongest_version": data.get("strongest_version", ""),
            "gap": data.get("gap", ""),
            "opponent_recognition": data.get("opponent_recognition", ""),
            "improvements": data.get("improvements", ""),
            "recommendation": data.get("recommendation", ""),
        }
