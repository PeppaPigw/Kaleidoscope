"""EpistemicTemporalPresentismService - Epistemic Temporal Presentism Detection.

Detects presentism bias projecting current values or knowledge onto past or future.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_PRESENTISM_SYSTEM = """You are an epistemic temporal presentism specialist. Given present projection, assess presentism bias:

Key concepts:
- Epistemic temporal presentism: projecting current values or knowledge onto past or future
- Present projection: treating current assumptions as timeless
- Anachronistic judgment: judging other times by present standards
- Context stripping: removing period constraints and available knowledge
- Temporal chauvinism: treating the present as epistemically superior by default

When epistemic temporal presentism IS present:
- Current values projected across time
- Current knowledge assumed available
- Anachronistic judgments made
- Historical or future context stripped
- Present treated as the privileged standard

When no presentism:
- Time-specific context preserved
- Available knowledge distinguished from current knowledge
- Period-appropriate standards considered
- Future uncertainty acknowledged
- Present assumptions treated as contingent

Output JSON with: presentism_detected (bool), severity (none/mild/moderate/severe), anachronistic_judgment (what present judgment imposed), context_stripping (what temporal context stripped), temporal_chauvinism (what present superiority assumed), recommendation (no_presentism/mild_temporal_awareness/significant_context_restoration/major_temporal_reconstruction/emergency_complete_presentism)."""

EPISTEMIC_TEMPORAL_PRESENTISM_PROMPT = """Detect epistemic temporal presentism:

Present projection: {present_projection}
Anachronistic judgment: {anachronistic_judgment}
Context stripping: {context_stripping}
Temporal chauvinism: {temporal_chauvinism}
Domain: {domain}
Context: {context}

Are current values or knowledge being projected onto another time? Return ONLY valid JSON."""


class EpistemicTemporalPresentismService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        present_projection: str,
        *,
        anachronistic_judgment: str = "",
        context_stripping: str = "",
        temporal_chauvinism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_PRESENTISM_PROMPT.format(
                present_projection=present_projection,
                anachronistic_judgment=anachronistic_judgment or "Not specified",
                context_stripping=context_stripping or "Not specified",
                temporal_chauvinism=temporal_chauvinism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_PRESENTISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "present_projection": present_projection[:200],
            "presentism_detected": data.get("presentism_detected", False),
            "severity": data.get("severity", ""),
            "anachronistic_judgment": data.get("anachronistic_judgment", ""),
            "context_stripping": data.get("context_stripping", ""),
            "temporal_chauvinism": data.get("temporal_chauvinism", ""),
            "recommendation": data.get("recommendation", ""),
        }
