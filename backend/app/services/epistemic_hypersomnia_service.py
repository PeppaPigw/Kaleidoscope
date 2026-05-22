"""EpistemicHypersomniaService — Epistemic Hypersomnia Detection.

Detects epistemic hypersomnia — excessive intellectual dormancy with
inability to maintain wakefulness despite adequate rest.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYPERSOMNIA_SYSTEM = """You are an epistemic hypersomnia specialist. Given excessive intellectual dormancy, assess hypersomnia patterns:

Key concepts:
- Epistemic hypersomnia: excessive intellectual dormancy
- Excessive sleepiness: overwhelming urge to disengage intellectually
- Sleep drunkenness: prolonged confusion upon intellectual awakening
- Non-restorative: rest does not restore intellectual function
- Prolonged episodes: extended periods of intellectual inactivity
- Functional impairment: dormancy interfering with obligations
- Idiopathic: no identifiable cause for excessive dormancy

When epistemic hypersomnia IS present:
- Excessive intellectual dormancy
- Overwhelming urge to disengage
- Prolonged confusion upon awakening
- Rest not restoring function
- Extended inactivity periods
- Dormancy interfering with obligations
- No identifiable cause

When no hypersomnia:
- Appropriate intellectual activity
- Normal engagement levels
- Clear awakening
- Rest restores function
- Normal activity periods
- Meeting obligations
- Clear causes for any rest

Output JSON with: hypersomnia_detected (bool), severity (none/mild/moderate/severe), dormancy_pattern (what excessive rest), awakening_difficulty (what confusion), functional_impact (what impairment), restorative_quality (what recovery), recommendation (no_hypersomnia/mild_scheduled_activity/significant_stimulant_equivalent/major_intensive_program/emergency_complete_dormancy)."""

EPISTEMIC_HYPERSOMNIA_PROMPT = """Detect epistemic hypersomnia:

Dormancy pattern: {dormancy_pattern}
Awakening difficulty: {awakening_difficulty}
Functional impact: {functional_impact}
Restorative quality: {restorative_quality}
Domain: {domain}
Context: {context}

Is there excessive intellectual dormancy with inability to maintain wakefulness? Return ONLY valid JSON."""


class EpistemicHypersomniaService:
    """Detects epistemic hypersomnia — excessive intellectual dormancy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dormancy_pattern: str,
        *,
        awakening_difficulty: str = "",
        functional_impact: str = "",
        restorative_quality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hypersomnia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYPERSOMNIA_PROMPT.format(
                dormancy_pattern=dormancy_pattern,
                awakening_difficulty=awakening_difficulty or "Not specified",
                functional_impact=functional_impact or "Not specified",
                restorative_quality=restorative_quality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYPERSOMNIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dormancy_pattern": dormancy_pattern[:200],
            "hypersomnia_detected": data.get("hypersomnia_detected", False),
            "severity": data.get("severity", ""),
            "awakening_difficulty": data.get("awakening_difficulty", ""),
            "functional_impact": data.get("functional_impact", ""),
            "restorative_quality": data.get("restorative_quality", ""),
            "recommendation": data.get("recommendation", ""),
        }
