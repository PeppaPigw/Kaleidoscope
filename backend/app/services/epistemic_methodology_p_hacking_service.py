"""EpistemicMethodologyPHackingService - Epistemic Methodology P-Hacking Detection.

Detects p-hacking and data dredging producing spurious statistical significance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METHODOLOGY_P_HACKING_SYSTEM = """You are an epistemic methodology p-hacking specialist. Given multiple testing abuse, assess p-hacking:

Key concepts:
- Epistemic methodology p-hacking: data dredging producing spurious statistical significance
- Multiple testing abuse: trying many analyses without correction
- Outcome switching: changing target outcomes after seeing data
- Selective reporting: reporting only significant or favorable results
- Garden of forking paths: undisclosed analytic flexibility creating false positives

When p-hacking IS present:
- Multiple testing is abused
- Outcomes are switched
- Results are selectively reported
- Analytic paths are chosen after seeing data
- Statistical significance is likely spurious

When no p-hacking:
- Analyses are pre-specified or corrected
- Outcomes remain stable
- Reporting is complete
- Analytic flexibility is disclosed
- Significance is interpreted cautiously

Output JSON with: p_hacking_detected (bool), severity (none/mild/moderate/severe), outcome_switching (what outcomes were switched), selective_reporting (what reporting is selective), garden_of_forking_paths (what analytic flexibility appears), recommendation (no_p_hacking/mild_multiple_testing_check/significant_correction_needed/major_preregistration_review/emergency_complete_p_hacking)."""

EPISTEMIC_METHODOLOGY_P_HACKING_PROMPT = """Detect epistemic methodology p-hacking:

Multiple testing abuse: {multiple_testing_abuse}
Outcome switching: {outcome_switching}
Selective reporting: {selective_reporting}
Garden of forking paths: {garden_of_forking_paths}
Domain: {domain}
Context: {context}

Are p-hacking or data dredging producing spurious statistical significance? Return ONLY valid JSON."""


class EpistemicMethodologyPHackingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        multiple_testing_abuse: str,
        *,
        outcome_switching: str = "",
        selective_reporting: str = "",
        garden_of_forking_paths: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METHODOLOGY_P_HACKING_PROMPT.format(
                multiple_testing_abuse=multiple_testing_abuse,
                outcome_switching=outcome_switching or "Not specified",
                selective_reporting=selective_reporting or "Not specified",
                garden_of_forking_paths=garden_of_forking_paths or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METHODOLOGY_P_HACKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "multiple_testing_abuse": multiple_testing_abuse[:200],
            "p_hacking_detected": data.get("p_hacking_detected", False),
            "severity": data.get("severity", ""),
            "outcome_switching": data.get("outcome_switching", ""),
            "selective_reporting": data.get("selective_reporting", ""),
            "garden_of_forking_paths": data.get("garden_of_forking_paths", ""),
            "recommendation": data.get("recommendation", ""),
        }
