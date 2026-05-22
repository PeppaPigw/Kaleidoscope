"""DurationNeglectService — Duration Neglect Detection.

Detects duration neglect — ignoring the duration of an experience
when evaluating it. Kahneman et al. (1993). People judge
experiences by their peak intensity and how they end (peak-end
rule), largely ignoring how long the experience lasted. A 60-second
painful procedure is remembered as worse than a 90-second one
if the extra 30 seconds were less painful.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DURATION_NEGLECT_SYSTEM = """You are a duration neglect specialist. Given an evaluation of an experience or event, assess whether duration is being inappropriately ignored:

Key concepts (Kahneman et al., 1993):
- Duration neglect: ignoring how long an experience lasted
- Peak-end rule: judging by peak intensity and ending
- Remembered utility vs experienced utility: memory distorts duration
- Snapshot model: evaluating moments not totals
- Cold water experiment: longer painful experience preferred if ending is better
- Colonoscopy study: longer procedure rated better with gradual ending
- Vacation paradox: a week vs two weeks rated similarly

When duration neglect IS present:
- Judging a long positive experience same as a brief one
- Rating a brief intense negative experience worse than a prolonged mild one
- Ignoring cumulative impact over time
- "It was terrible" based on one bad moment in an otherwise good period
- Evaluating projects by their ending, not their total contribution
- Preferring intense brief experiences over sustained moderate ones
- Ignoring that chronic low-level problems accumulate

When duration IS appropriately weighted:
- Considering total time invested in evaluations
- Recognizing that sustained experiences have cumulative effects
- Distinguishing between brief peaks and prolonged states
- Accounting for duration when comparing experiences
- Recognizing that chronic issues matter more than acute ones

Output JSON with: duration_neglect_present (bool), severity (none/mild/moderate/severe), evaluation (what is being evaluated), duration_ignored (what duration is being neglected), peak_focus (what peak moment dominates the evaluation), end_focus (how does the ending dominate), actual_duration (what was the actual duration), duration_impact (how should duration change the evaluation), recommendation (duration_appropriately_weighted/mild_duration_neglect/significant_peak_end_dominance/major_duration_ignored/weight_total_duration)."""

DURATION_NEGLECT_PROMPT = """Detect duration neglect:

Evaluation: {evaluation}
Experience: {experience}
Duration: {duration}
Peak moments: {peaks}
Domain: {domain}
Context: {context}

Is the duration of the experience being inappropriately ignored in favor of peak moments or endings? Return ONLY valid JSON."""


class DurationNeglectService:
    """Detects duration neglect — ignoring experience duration in evaluations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        experience: str = "",
        duration: str = "",
        peaks: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect duration neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DURATION_NEGLECT_PROMPT.format(
                evaluation=evaluation,
                experience=experience or "Not specified",
                duration=duration or "Not specified",
                peaks=peaks or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DURATION_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "duration_neglect_present": data.get("duration_neglect_present", False),
            "severity": data.get("severity", ""),
            "duration_ignored": data.get("duration_ignored", ""),
            "peak_focus": data.get("peak_focus", ""),
            "end_focus": data.get("end_focus", ""),
            "actual_duration": data.get("actual_duration", ""),
            "duration_impact": data.get("duration_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
