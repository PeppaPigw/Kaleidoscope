"""SelfModelErrorService — Self-Model Error Detection.

Detects self-model error — having an inaccurate model of one's own
beliefs, values, or decision processes, where stated preferences
diverge from revealed preferences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELF_MODEL_ERROR_SYSTEM = """You are a self-model error specialist. Given a self-description and behavior, assess whether someone's self-model is inaccurate:

Key concepts:
- Self-model error: inaccurate model of own beliefs/values
- Stated vs. revealed preferences: what you say vs. what you do
- Self-deception: maintaining false beliefs about oneself
- Narrative identity: story about self that doesn't match reality
- Value-action gap: stated values not reflected in behavior
- Self-serving self-model: flattering but inaccurate self-image
- Behavioral evidence: actions revealing actual preferences

When self-model error IS present:
- Stated beliefs contradicted by behavior
- Self-description inconsistent with observable actions
- Values claimed but not enacted
- Decision processes described don't match actual decisions
- Self-model serves ego rather than accuracy
- Revealed preferences diverge from stated preferences
- Behavioral patterns contradict self-narrative

When self-model is appropriate:
- Stated preferences consistent with behavior
- Self-description matches observable actions
- Values reflected in actual choices
- Self-model updated based on behavioral evidence
- Discrepancies acknowledged when noticed
- Self-knowledge appropriately uncertain
- Aspirational vs. actual clearly distinguished

Output JSON with: error_present (bool), severity (none/mild/moderate/severe), self_model (what is claimed about self), behavioral_evidence (what behavior shows), discrepancy (where model and behavior diverge), function (what purpose the inaccurate model serves), recommendation (appropriate_self_model/mild_self_flattery/significant_self_model_error/major_self_deception/align_model_with_behavior)."""

SELF_MODEL_ERROR_PROMPT = """Detect self-model error:

Self-description: {description}
Behavior observed: {behavior}
Values claimed: {values}
Actions taken: {actions}
Domain: {domain}
Context: {context}

Is there a significant discrepancy between self-model and actual behavior? Return ONLY valid JSON."""


class SelfModelErrorService:
    """Detects self-model error — inaccurate model of own beliefs and values."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        description: str,
        *,
        behavior: str = "",
        values: str = "",
        actions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect self-model error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELF_MODEL_ERROR_PROMPT.format(
                description=description,
                behavior=behavior or "Not specified",
                values=values or "Not specified",
                actions=actions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELF_MODEL_ERROR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "description": description[:200],
            "error_present": data.get("error_present", False),
            "severity": data.get("severity", ""),
            "self_model": data.get("self_model", ""),
            "behavioral_evidence": data.get("behavioral_evidence", ""),
            "discrepancy": data.get("discrepancy", ""),
            "recommendation": data.get("recommendation", ""),
        }
