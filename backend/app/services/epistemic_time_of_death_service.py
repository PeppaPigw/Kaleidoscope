"""EpistemicTimeOfDeathService — Epistemic Time of Death Detection.

Detects epistemic time of death — establishing when intellectual vitality
was lost, the moment function ceased.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TIME_OF_DEATH_SYSTEM = """You are an epistemic time of death specialist. Given intellectual failure timeline, establish when vitality was lost:

Key concepts:
- Epistemic time of death: when intellectual vitality was lost
- Rigor: stiffening after death indicating time elapsed
- Livor: settling of intellectual substance indicating position at death
- Algor: cooling rate indicating time since death
- Witness accounts: last known alive observations
- Scene evidence: environmental clues to timing
- Decomposition rate: decay speed indicating elapsed time

When epistemic time of death IS estimable:
- Clear indicators of when vitality was lost
- Stiffening indicating time elapsed since death
- Settling indicating position at time of death
- Cooling rate indicating time since death
- Last known alive observations available
- Environmental clues to timing present
- Decay speed indicating elapsed time

When time unclear:
- No clear indicators of timing
- No stiffening pattern
- No settling pattern
- No cooling data
- No witness accounts
- No environmental clues
- No decay rate data

Output JSON with: time_of_death_estimable (bool), severity (none/mild/moderate/severe), rigor (what stiffening pattern), livor (what settling pattern), algor (what cooling rate), witness_accounts (what last alive), recommendation (time_unclear/mild_estimation/significant_time_established/major_precise_timing/document_intellectual_time_of_death)."""

EPISTEMIC_TIME_OF_DEATH_PROMPT = """Detect epistemic time of death:

Rigor: {rigor}
Livor: {livor}
Algor: {algor}
Witness accounts: {witness_accounts}
Domain: {domain}
Context: {context}

When was intellectual vitality lost? Return ONLY valid JSON."""


class EpistemicTimeOfDeathService:
    """Detects epistemic time of death — when intellectual vitality was lost."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        rigor: str,
        *,
        livor: str = "",
        algor: str = "",
        witness_accounts: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic time of death."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TIME_OF_DEATH_PROMPT.format(
                rigor=rigor,
                livor=livor or "Not specified",
                algor=algor or "Not specified",
                witness_accounts=witness_accounts or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TIME_OF_DEATH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "rigor": rigor[:200],
            "time_of_death_estimable": data.get("time_of_death_estimable", False),
            "severity": data.get("severity", ""),
            "livor": data.get("livor", ""),
            "algor": data.get("algor", ""),
            "witness_accounts": data.get("witness_accounts", ""),
            "recommendation": data.get("recommendation", ""),
        }
