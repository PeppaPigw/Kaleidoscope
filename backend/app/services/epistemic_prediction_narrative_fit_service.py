"""EpistemicPredictionNarrativeFitService — Epistemic Prediction Narrative Fit Detection.

Detects epistemic prediction narrative fit — predictions shaped by narrative coherence
and storytelling rather than statistical base rates and evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PREDICTION_NARRATIVE_FIT_SYSTEM = """You are an epistemic prediction narrative fit specialist. Given narrative-driven predictions, assess story-over-statistics distortion:

Key concepts:
- Epistemic prediction narrative fit: predictions driven by story not statistics
- Scenario thinking: vivid scenarios overriding base rates
- Representativeness: predictions based on how representative a story seems
- Conjunction fallacy: detailed predictions seeming more likely than simple ones
- Narrative momentum: predictions following story arc not evidence
- Character-driven prediction: predicting based on character not situation
- Plot expectation: expecting reality to follow narrative conventions

When epistemic prediction narrative fit IS present:
- Predictions driven by story
- Vivid scenarios overriding base rates
- Representativeness driving prediction
- Detailed predictions seeming more likely
- Story arc driving prediction
- Character over situation
- Plot conventions expected

When no narrative fit bias:
- Predictions driven by evidence
- Base rates incorporated
- Statistical reasoning applied
- Simplicity appropriately valued
- Evidence driving prediction
- Situation properly weighted
- Reality not expected to follow plots

Output JSON with: narrative_fit_detected (bool), severity (none/mild/moderate/severe), scenario_over_base_rate (what scenarios overriding), representativeness_driving (what representativeness driving), conjunction_fallacy (what detailed predictions inflated), narrative_momentum (what story arc driving), recommendation (no_narrative_fit/mild_base_rate_checking/significant_statistical_anchoring/major_intensive_reference_class_analysis/emergency_complete_narrative_fit)."""

EPISTEMIC_PREDICTION_NARRATIVE_FIT_PROMPT = """Detect epistemic prediction narrative fit:

Scenario over base rate: {scenario_over_base_rate}
Representativeness driving: {representativeness_driving}
Conjunction fallacy: {conjunction_fallacy}
Narrative momentum: {narrative_momentum}
Domain: {domain}
Context: {context}

Are predictions shaped by narrative coherence rather than base rates? Return ONLY valid JSON."""


class EpistemicPredictionNarrativeFitService:
    """Detects epistemic prediction narrative fit — story over statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        scenario_over_base_rate: str,
        *,
        representativeness_driving: str = "",
        conjunction_fallacy: str = "",
        narrative_momentum: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic prediction narrative fit."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PREDICTION_NARRATIVE_FIT_PROMPT.format(
                scenario_over_base_rate=scenario_over_base_rate,
                representativeness_driving=representativeness_driving or "Not specified",
                conjunction_fallacy=conjunction_fallacy or "Not specified",
                narrative_momentum=narrative_momentum or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PREDICTION_NARRATIVE_FIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "scenario_over_base_rate": scenario_over_base_rate[:200],
            "narrative_fit_detected": data.get("narrative_fit_detected", False),
            "severity": data.get("severity", ""),
            "representativeness_driving": data.get("representativeness_driving", ""),
            "conjunction_fallacy": data.get("conjunction_fallacy", ""),
            "narrative_momentum": data.get("narrative_momentum", ""),
            "recommendation": data.get("recommendation", ""),
        }
