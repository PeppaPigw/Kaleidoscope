"""EpistemicBenignEnvyService — Epistemic Benign Envy Detection.

Detects epistemic benign envy — motivating envy that drives self-improvement
but causes distress through unfavorable comparison.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BENIGN_ENVY_SYSTEM = """You are an epistemic benign envy specialist. Given motivating but distressing envy, assess benign envy:

Key concepts:
- Epistemic benign envy: motivating but distressing comparison
- Upward comparison: measuring self against superior others
- Aspiration pain: wanting what others have intellectually
- Self-inadequacy: feeling less than in comparison
- Motivation driver: envy pushing toward improvement
- Chronic dissatisfaction: never good enough compared to others
- Moving goalpost: achievement doesn't resolve the envy

When epistemic benign envy IS present:
- Motivating but distressing
- Measuring against superior
- Wanting what others have
- Feeling less than
- Pushing toward improvement
- Never good enough
- Achievement doesn't resolve

When no benign envy:
- Self-referenced standards
- Not comparing
- Content with own path
- Feeling adequate
- Intrinsic motivation
- Satisfied with progress
- Achievement satisfies

Output JSON with: benign_envy_detected (bool), severity (none/mild/moderate/severe), upward_comparison (what measuring against), aspiration_pain (what wanting), self_inadequacy (what feeling less), chronic_dissatisfaction (what never enough), recommendation (no_benign_envy/mild_comparison_awareness/significant_self_reference_building/major_intensive_adequacy_work/emergency_severe_distress)."""

EPISTEMIC_BENIGN_ENVY_PROMPT = """Detect epistemic benign envy:

Upward comparison: {upward_comparison}
Aspiration pain: {aspiration_pain}
Self inadequacy: {self_inadequacy}
Chronic dissatisfaction: {chronic_dissatisfaction}
Domain: {domain}
Context: {context}

Is there motivating envy causing distress through unfavorable comparison? Return ONLY valid JSON."""


class EpistemicBenignEnvyService:
    """Detects epistemic benign envy — motivating but distressing comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        upward_comparison: str,
        *,
        aspiration_pain: str = "",
        self_inadequacy: str = "",
        chronic_dissatisfaction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic benign envy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BENIGN_ENVY_PROMPT.format(
                upward_comparison=upward_comparison,
                aspiration_pain=aspiration_pain or "Not specified",
                self_inadequacy=self_inadequacy or "Not specified",
                chronic_dissatisfaction=chronic_dissatisfaction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BENIGN_ENVY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "upward_comparison": upward_comparison[:200],
            "benign_envy_detected": data.get("benign_envy_detected", False),
            "severity": data.get("severity", ""),
            "aspiration_pain": data.get("aspiration_pain", ""),
            "self_inadequacy": data.get("self_inadequacy", ""),
            "chronic_dissatisfaction": data.get("chronic_dissatisfaction", ""),
            "recommendation": data.get("recommendation", ""),
        }
