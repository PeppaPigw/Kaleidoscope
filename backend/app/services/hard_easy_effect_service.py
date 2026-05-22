"""HardEasyEffectService — Hard-Easy Effect Detection.

Detects hard-easy effect — tendency to be overconfident on
hard questions and underconfident on easy questions.
Lichtenstein & Fischhoff (1977). People say "90% sure" on
hard questions where they're right only 60% of the time,
and "60% sure" on easy questions where they're right 90%.
Confidence doesn't track difficulty appropriately.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HARD_EASY_SYSTEM = """You are a hard-easy effect specialist. Given a confidence judgment, assess whether confidence is appropriately calibrated to task difficulty:

Key concepts (Lichtenstein & Fischhoff, 1977):
- Hard-easy effect: overconfidence on hard tasks, underconfidence on easy ones
- Calibration: match between confidence and accuracy
- Difficulty insensitivity: confidence doesn't adjust enough for difficulty
- Anchoring on moderate confidence: defaulting to 70-80% regardless
- Domain expertise interaction: experts may be better calibrated
- Regression to mean confidence: extreme confidence/doubt are rare
- Dunning-Kruger interaction: not knowing what you don't know

When hard-easy effect IS present:
- High confidence on genuinely difficult/uncertain questions
- Low confidence on questions where the answer is clearly known
- Confidence level similar across very different difficulty levels
- "I'm pretty sure" on both trivial and complex questions
- Not adjusting confidence when moving from easy to hard domains
- Treating all estimates with similar confidence regardless of basis

When the confidence IS calibrated:
- Confidence tracks actual accuracy across difficulty levels
- The person adjusts confidence appropriately for harder questions
- Easy questions get high confidence, hard questions get low confidence
- The person has demonstrated calibration in similar domains
- Confidence reflects genuine assessment of knowledge quality

Output JSON with: hard_easy_effect_present (bool), severity (none/mild/moderate/severe), judgment (what judgment is being made), stated_confidence (what confidence is expressed), task_difficulty (how difficult is the task), expected_accuracy (what accuracy would calibration predict), calibration_gap (difference between confidence and expected accuracy), direction (overconfident_on_hard/underconfident_on_easy/both), recommendation (confidence_calibrated/mild_miscalibration/significant_hard_easy/major_calibration_failure/adjust_for_difficulty)."""

HARD_EASY_PROMPT = """Detect hard-easy effect:

Judgment: {judgment}
Confidence: {confidence}
Difficulty: {difficulty}
Track record: {track_record}
Domain: {domain}
Context: {context}

Is confidence appropriately calibrated to task difficulty? Return ONLY valid JSON."""


class HardEasyEffectService:
    """Detects hard-easy effect — overconfidence on hard, underconfidence on easy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        confidence: str = "",
        difficulty: str = "",
        track_record: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hard-easy effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HARD_EASY_PROMPT.format(
                judgment=judgment,
                confidence=confidence or "Not specified",
                difficulty=difficulty or "Not specified",
                track_record=track_record or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HARD_EASY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "hard_easy_effect_present": data.get("hard_easy_effect_present", False),
            "severity": data.get("severity", ""),
            "stated_confidence": data.get("stated_confidence", ""),
            "task_difficulty": data.get("task_difficulty", ""),
            "expected_accuracy": data.get("expected_accuracy", ""),
            "calibration_gap": data.get("calibration_gap", ""),
            "direction": data.get("direction", ""),
            "recommendation": data.get("recommendation", ""),
        }
