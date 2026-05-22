"""AbsenceBlindnessService — Absence Blindness Detection.

Detects absence blindness — the systematic failure to notice
what's missing, what didn't happen, or what's not there.
Related to the feature-positive effect but focused specifically
on decision-making contexts where critical absences go undetected.
The most dangerous risks are often the ones nobody thought to
look for.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ABSENCE_BLINDNESS_SYSTEM = """You are an absence blindness specialist. Given a decision or evaluation context, assess whether critical absences are going unnoticed:

Key concepts:
- Absence blindness: failing to notice what's not there
- Non-occurrence: events that didn't happen are invisible
- Missing evidence: absence of evidence treated as evidence of absence
- Survivorship bias interaction: only seeing what survived
- Silent evidence: data from failures/non-events is lost
- Negative space: what's not said/done/present
- Pre-mortem gap: failure modes nobody imagined

When absence blindness IS present:
- No one asking "what's missing from this analysis?"
- Evaluating only visible outcomes, not invisible non-events
- "Everything looks good" without checking for gaps
- Risk assessment that only considers known threats
- Post-mortem that only examines what happened, not what didn't
- Decision based on available evidence without noting what evidence is absent
- "We haven't seen any problems" when problems would be invisible

When the evaluation IS complete:
- Explicit effort to identify what's missing
- Pre-mortem or red team exercises conducted
- Absence of evidence explicitly noted as uncertainty
- Systematic check for what should be present but isn't
- "What would we expect to see if X were true?" analysis

Output JSON with: absence_blindness_present (bool), severity (none/mild/moderate/severe), context (what is being evaluated), critical_absences (what important things are missing), detection_difficulty (why are absences hard to notice), consequences (what could go wrong due to missed absences), systematic_check (was any check for absences performed), invisible_risks (what risks are invisible due to absence blindness), recommendation (evaluation_complete/mild_absence_gap/significant_absence_blindness/major_critical_gaps_missed/systematically_check_for_absences)."""

ABSENCE_BLINDNESS_PROMPT = """Detect absence blindness:

Context: {context_input}
What's present: {present}
What might be missing: {missing}
Checks performed: {checks}
Domain: {domain}
Context: {context}

Are critical absences going unnoticed in this evaluation or decision? Return ONLY valid JSON."""


class AbsenceBlindnessService:
    """Detects absence blindness — failing to notice what's missing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        context_input: str,
        *,
        present: str = "",
        missing: str = "",
        checks: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect absence blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABSENCE_BLINDNESS_PROMPT.format(
                context_input=context_input,
                present=present or "Not specified",
                missing=missing or "Not specified",
                checks=checks or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ABSENCE_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "context_input": context_input[:200],
            "absence_blindness_present": data.get("absence_blindness_present", False),
            "severity": data.get("severity", ""),
            "critical_absences": data.get("critical_absences", ""),
            "detection_difficulty": data.get("detection_difficulty", ""),
            "consequences": data.get("consequences", ""),
            "systematic_check": data.get("systematic_check", ""),
            "invisible_risks": data.get("invisible_risks", ""),
            "recommendation": data.get("recommendation", ""),
        }
