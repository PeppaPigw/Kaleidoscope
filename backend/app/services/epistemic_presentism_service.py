"""EpistemicPresentismService — Epistemic Presentism Detection.

Detects epistemic presentism — judging past knowledge by present
standards unfairly, failing to account for what was knowable at the time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRESENTISM_SYSTEM = """You are an epistemic presentism specialist. Given a historical judgment, assess whether past knowledge is being unfairly judged by present standards:

Key concepts:
- Epistemic presentism: judging past knowledge by present standards
- Hindsight unfairness: unfairly applying hindsight to past decisions
- Knowability neglect: ignoring what was knowable at the time
- Temporal arrogance: assuming present knowledge is obviously superior
- Context stripping: stripping historical context from past beliefs
- Anachronistic standards: applying anachronistic epistemic standards
- Progress narrative: assuming linear progress makes past inferior

When epistemic presentism IS present:
- Past knowledge judged unfairly by present standards
- Hindsight applied without acknowledging what was knowable
- Historical context stripped from past beliefs
- Temporal arrogance about present superiority
- Anachronistic standards applied to past inquiry
- Progress narrative making past seem obviously wrong
- Failure to account for available evidence at the time

When appropriate historical assessment is present:
- Past knowledge assessed in its own context
- Hindsight acknowledged and accounted for
- Historical context preserved in assessment
- Present knowledge recognized as also provisional
- Standards appropriate to the era applied
- Progress acknowledged without arrogance
- Available evidence at the time considered

Output JSON with: presentism_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is made), past_context (what context is ignored), present_standard (what present standard is applied), unfairness (how judgment is unfair), recommendation (appropriate_assessment/mild_hindsight/significant_epistemic_presentism/major_temporal_arrogance/assess_in_historical_context)."""

EPISTEMIC_PRESENTISM_PROMPT = """Detect epistemic presentism:

Judgment: {judgment}
Past context: {past_context}
Present standard: {standard}
Knowability: {knowability}
Domain: {domain}
Context: {context}

Is past knowledge being unfairly judged by present standards? Return ONLY valid JSON."""


class EpistemicPresentismService:
    """Detects epistemic presentism — judging past by present standards unfairly."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        past_context: str = "",
        standard: str = "",
        knowability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic presentism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRESENTISM_PROMPT.format(
                judgment=judgment,
                past_context=past_context or "Not specified",
                standard=standard or "Not specified",
                knowability=knowability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRESENTISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "presentism_present": data.get("presentism_present", False),
            "severity": data.get("severity", ""),
            "past_context": data.get("past_context", ""),
            "present_standard": data.get("present_standard", ""),
            "unfairness": data.get("unfairness", ""),
            "recommendation": data.get("recommendation", ""),
        }
