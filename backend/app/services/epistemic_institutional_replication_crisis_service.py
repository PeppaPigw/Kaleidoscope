"""EpistemicInstitutionalReplicationCrisisService — Epistemic Replication Crisis Detection.

Detects epistemic institutional replication crisis — failure to replicate
findings indicating systemic problems in knowledge production.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_REPLICATION_CRISIS_SYSTEM = """You are an epistemic institutional replication crisis specialist. Given replication failures, assess systemic problems:

Key concepts:
- Epistemic replication crisis: failure to replicate indicating systemic issues
- Low replication rates: findings failing to replicate at high rates
- Methodological flexibility: researcher degrees of freedom enabling false positives
- Underpowered studies: studies too small to detect real effects
- Publication bias: only positive results published creating false literature
- Effect size inflation: initial studies overestimating effect sizes
- Decline effect: effects shrinking as more studies conducted

When epistemic replication crisis IS present:
- Findings failing to replicate
- Methodological flexibility exploited
- Studies underpowered
- Publication bias active
- Effect sizes inflated
- Decline effect present
- Systemic problems indicated

When no replication crisis:
- Findings replicate reliably
- Methods pre-registered
- Studies adequately powered
- All results published
- Effect sizes stable
- No decline effect
- Knowledge production healthy

Output JSON with: replication_crisis_detected (bool), severity (none/mild/moderate/severe), low_replication_rate (what replication failures), methodological_flexibility (what flexibility exploited), underpowered_studies (what underpowered), effect_size_inflation (what effect sizes inflated), recommendation (no_replication_crisis/mild_replication_awareness/significant_preregistration/major_intensive_replication_program/emergency_complete_replication_crisis)."""

EPISTEMIC_INSTITUTIONAL_REPLICATION_CRISIS_PROMPT = """Detect epistemic institutional replication crisis:

Low replication rate: {low_replication_rate}
Methodological flexibility: {methodological_flexibility}
Underpowered studies: {underpowered_studies}
Effect size inflation: {effect_size_inflation}
Domain: {domain}
Context: {context}

Is failure to replicate findings indicating systemic problems? Return ONLY valid JSON."""


class EpistemicInstitutionalReplicationCrisisService:
    """Detects epistemic replication crisis — systemic knowledge production failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        low_replication_rate: str,
        *,
        methodological_flexibility: str = "",
        underpowered_studies: str = "",
        effect_size_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic institutional replication crisis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_REPLICATION_CRISIS_PROMPT.format(
                low_replication_rate=low_replication_rate,
                methodological_flexibility=methodological_flexibility or "Not specified",
                underpowered_studies=underpowered_studies or "Not specified",
                effect_size_inflation=effect_size_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_REPLICATION_CRISIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "low_replication_rate": low_replication_rate[:200],
            "replication_crisis_detected": data.get("replication_crisis_detected", False),
            "severity": data.get("severity", ""),
            "methodological_flexibility": data.get("methodological_flexibility", ""),
            "underpowered_studies": data.get("underpowered_studies", ""),
            "effect_size_inflation": data.get("effect_size_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
