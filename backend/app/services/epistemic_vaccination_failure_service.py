"""EpistemicVaccinationFailureService — Epistemic Vaccination Failure Detection.

Detects epistemic vaccination failure — exposure to weak
counterarguments creating false immunity to strong ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VACCINATION_FAILURE_SYSTEM = """You are an epistemic vaccination failure specialist. Given a belief defense pattern, assess whether weak counterargument exposure creates false immunity:

Key concepts:
- Epistemic vaccination failure: weak exposure creating false immunity
- Inoculation effect: exposure to weak version preventing response to strong
- False immunity: believing oneself immune when actually vulnerable
- Straw man inoculation: defeating straw men creating false confidence
- Premature closure: closing mind after defeating weak version
- Challenge underestimation: underestimating real challenges
- Defense theater: performing defense without actual protection

When epistemic vaccination failure IS present:
- Weak counterargument exposure creating false immunity
- Exposure to weak version preventing engagement with strong
- Believing oneself immune when actually vulnerable
- Defeating straw men creating false confidence
- Closing mind after defeating weak version of challenge
- Underestimating real challenges after defeating weak ones
- Performing defense without actual protection

When genuine resilience is present:
- Engagement with strongest counterarguments
- Immunity based on defeating strong challenges
- Confidence based on genuine testing
- Engaging with steelmanned versions
- Mind open to stronger challenges
- Accurately assessing challenge strength
- Defense based on genuine engagement

Output JSON with: vaccination_failure_present (bool), severity (none/mild/moderate/severe), pattern (what defense pattern exists), weak_exposure (what weak exposure occurred), false_immunity (what false immunity results), real_vulnerability (what real vulnerability remains), recommendation (genuine_resilience/mild_overconfidence/significant_vaccination_failure/major_false_immunity/engage_strongest_challenges)."""

EPISTEMIC_VACCINATION_FAILURE_PROMPT = """Detect epistemic vaccination failure:

Pattern: {pattern}
Weak exposure: {weak_exposure}
False immunity: {false_immunity}
Real vulnerability: {real_vulnerability}
Domain: {domain}
Context: {context}

Does weak counterargument exposure create false immunity to strong ones? Return ONLY valid JSON."""


class EpistemicVaccinationFailureService:
    """Detects epistemic vaccination failure — false immunity from weak exposure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        weak_exposure: str = "",
        false_immunity: str = "",
        real_vulnerability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic vaccination failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VACCINATION_FAILURE_PROMPT.format(
                pattern=pattern,
                weak_exposure=weak_exposure or "Not specified",
                false_immunity=false_immunity or "Not specified",
                real_vulnerability=real_vulnerability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VACCINATION_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "vaccination_failure_present": data.get("vaccination_failure_present", False),
            "severity": data.get("severity", ""),
            "weak_exposure": data.get("weak_exposure", ""),
            "false_immunity": data.get("false_immunity", ""),
            "real_vulnerability": data.get("real_vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
