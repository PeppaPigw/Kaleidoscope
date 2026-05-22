"""PeakEndService — Peak-End Rule Detection.

Detects the peak-end rule — judging experiences primarily by their
most intense moment (peak) and their ending, rather than by the
sum or average of every moment. Kahneman et al. (1993). Leads to
systematic misevaluation of experiences, policies, and processes.
Duration neglect is a key component.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PEAK_END_SYSTEM = """You are a peak-end rule specialist. Given an evaluation of an experience or process, assess whether the peak-end rule is distorting the assessment:

Key concepts (Kahneman et al., 1993):
- Peak-end rule: experiences judged by peak intensity and ending, not average
- Duration neglect: how long something lasted barely affects evaluation
- Remembered utility vs experienced utility: what we remember ≠ what we felt
- Recency bias component: endings disproportionately color memory
- Peak dominance: one extreme moment defines the whole experience
- Cold-water experiment: adding mild discomfort at end improves memory of painful experience

When the peak-end rule IS distorting:
- A long positive experience is rated poorly because of a bad ending
- A brief intense moment dominates evaluation of a long process
- Duration of positive/negative periods is being ignored
- The ending is being treated as representative of the whole
- Policy evaluation focuses on memorable moments, not cumulative impact

When peak-end evaluation IS appropriate:
- The peak genuinely represents the most important aspect
- The ending reflects the final state that persists
- Duration truly doesn't matter for the relevant outcome
- The evaluation is explicitly about memorable moments

Output JSON with: peak_end_present (bool), severity (none/mild/moderate/severe), experience_evaluated (what is being judged), peak_moment (what intense moment dominates the evaluation), ending (how the experience ended), duration (how long the experience lasted), duration_neglect (bool — is duration being ignored?), average_experience (what the typical moment was like), peak_vs_average_gap (how different the peak is from the average), ending_vs_average_gap (how different the ending is from the average), remembered_vs_experienced (how memory differs from actual experience), decision_impact (how peak-end evaluation affects future decisions), cumulative_assessment (what a duration-weighted evaluation would show), recommendation (evaluation_appropriate/mild_peak_end_bias/significant_distortion/major_duration_neglect/evaluate_cumulatively)."""

PEAK_END_PROMPT = """Detect peak-end rule:

Evaluation: {evaluation}
Experience details: {experience}
Peak moments: {peaks}
How it ended: {ending}
Domain: {domain}
Context: {context}

Is the peak-end rule distorting this evaluation? Return ONLY valid JSON."""


class PeakEndService:
    """Detects peak-end rule — judging by peaks and endings, not averages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        experience: str = "",
        peaks: str = "",
        ending: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect peak-end rule."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PEAK_END_PROMPT.format(
                evaluation=evaluation,
                experience=experience or "Not specified",
                peaks=peaks or "Not specified",
                ending=ending or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PEAK_END_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "peak_end_present": data.get("peak_end_present", False),
            "severity": data.get("severity", ""),
            "experience_evaluated": data.get("experience_evaluated", ""),
            "peak_moment": data.get("peak_moment", ""),
            "ending": data.get("ending", ""),
            "duration": data.get("duration", ""),
            "duration_neglect": data.get("duration_neglect", False),
            "average_experience": data.get("average_experience", ""),
            "peak_vs_average_gap": data.get("peak_vs_average_gap", ""),
            "ending_vs_average_gap": data.get("ending_vs_average_gap", ""),
            "remembered_vs_experienced": data.get("remembered_vs_experienced", ""),
            "decision_impact": data.get("decision_impact", ""),
            "cumulative_assessment": data.get("cumulative_assessment", ""),
            "recommendation": data.get("recommendation", ""),
        }
