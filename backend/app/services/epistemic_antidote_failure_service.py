"""EpistemicAntidoteFailureService — Epistemic Antidote Failure Detection.

Detects epistemic antidote failure — inability to neutralize intellectual
poison, where corrective measures fail to counteract toxic ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANTIDOTE_FAILURE_SYSTEM = """You are an epistemic antidote failure specialist. Given intellectual neutralization attempts, assess whether antidotes are failing:

Key concepts:
- Epistemic antidote failure: inability to neutralize intellectual poison
- Resistance: toxin evolved past antidote effectiveness
- Wrong antidote: misidentified poison requiring different counter
- Insufficient dose: not enough counteragent applied
- Delayed administration: antidote given too late
- Paradoxical reaction: antidote worsening the condition
- Antidote toxicity: cure itself causing harm

When epistemic antidote failure IS present:
- Inability to neutralize intellectual poison
- Toxin evolved past corrective effectiveness
- Misidentified problem requiring different approach
- Insufficient corrective measures applied
- Correction attempted too late
- Correction worsening the condition
- Cure itself causing intellectual harm

When successful neutralization is present:
- Effective neutralization of poison
- Antidote matches toxin
- Correct identification of problem
- Sufficient corrective dose
- Timely administration
- Expected beneficial response
- No iatrogenic harm

Output JSON with: antidote_failure_present (bool), severity (none/mild/moderate/severe), resistance (what evolved past), wrong_antidote (what misidentified), insufficient_dose (what not enough), paradoxical_reaction (what worsening), recommendation (successful_neutralization/mild_failure/significant_antidote_failure/major_neutralization_collapse/redesign_intellectual_antidote)."""

EPISTEMIC_ANTIDOTE_FAILURE_PROMPT = """Detect epistemic antidote failure:

Resistance: {resistance}
Wrong antidote: {wrong_antidote}
Insufficient dose: {insufficient_dose}
Paradoxical reaction: {paradoxical_reaction}
Domain: {domain}
Context: {context}

Are corrective measures failing to neutralize intellectual poison? Return ONLY valid JSON."""


class EpistemicAntidoteFailureService:
    """Detects epistemic antidote failure — inability to neutralize intellectual poison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        resistance: str,
        *,
        wrong_antidote: str = "",
        insufficient_dose: str = "",
        paradoxical_reaction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic antidote failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANTIDOTE_FAILURE_PROMPT.format(
                resistance=resistance,
                wrong_antidote=wrong_antidote or "Not specified",
                insufficient_dose=insufficient_dose or "Not specified",
                paradoxical_reaction=paradoxical_reaction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANTIDOTE_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "resistance": resistance[:200],
            "antidote_failure_present": data.get("antidote_failure_present", False),
            "severity": data.get("severity", ""),
            "wrong_antidote": data.get("wrong_antidote", ""),
            "insufficient_dose": data.get("insufficient_dose", ""),
            "paradoxical_reaction": data.get("paradoxical_reaction", ""),
            "recommendation": data.get("recommendation", ""),
        }
