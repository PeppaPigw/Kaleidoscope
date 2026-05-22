"""EpistemicMetacognitiveOverconfidenceService — Epistemic Metacognitive Overconfidence Detection.

Detects epistemic metacognitive overconfidence — overconfidence in one's
metacognitive accuracy, believing one knows how one thinks better than one does.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_METACOGNITIVE_OVERCONFIDENCE_SYSTEM = """You are an epistemic metacognitive overconfidence specialist. Given overconfidence in metacognitive accuracy, assess metacognitive overconfidence:

Key concepts:
- Epistemic metacognitive overconfidence: overconfidence in metacognitive accuracy
- Self-knowledge inflation: inflated belief in self-knowledge
- Introspection overconfidence: overconfident in introspective accuracy
- Monitoring overconfidence: overconfident in ability to monitor own thinking
- Correction overconfidence: overconfident in ability to correct own biases
- Calibration overconfidence: overconfident in own calibration
- Meta-accuracy inflation: inflated belief in meta-level accuracy

When epistemic metacognitive overconfidence IS present:
- Overconfident in metacognitive accuracy
- Self-knowledge inflated
- Introspection overconfident
- Monitoring overconfident
- Correction overconfident
- Calibration overconfident
- Meta-accuracy inflated

When no metacognitive overconfidence:
- Metacognitive accuracy calibrated
- Self-knowledge realistic
- Introspection humble
- Monitoring realistic
- Correction realistic
- Calibration honest
- Meta-accuracy realistic

Output JSON with: metacognitive_overconfidence_detected (bool), severity (none/mild/moderate/severe), self_knowledge_inflation (what self-knowledge inflated about), introspection_overconfidence (what introspection overconfident about), monitoring_overconfidence (what monitoring overconfident about), correction_overconfidence (what correction overconfident about), recommendation (no_metacognitive_overconfidence/mild_humility_practice/significant_calibration_correction/major_intensive_meta_accuracy_recovery/emergency_complete_metacognitive_overconfidence)."""

EPISTEMIC_METACOGNITIVE_OVERCONFIDENCE_PROMPT = """Detect epistemic metacognitive overconfidence:

Self-knowledge inflation: {self_knowledge_inflation}
Introspection overconfidence: {introspection_overconfidence}
Monitoring overconfidence: {monitoring_overconfidence}
Correction overconfidence: {correction_overconfidence}
Domain: {domain}
Context: {context}

Is there overconfidence in metacognitive accuracy? Return ONLY valid JSON."""


class EpistemicMetacognitiveOverconfidenceService:
    """Detects epistemic metacognitive overconfidence — overconfidence in meta-accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_knowledge_inflation: str,
        *,
        introspection_overconfidence: str = "",
        monitoring_overconfidence: str = "",
        correction_overconfidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic metacognitive overconfidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_METACOGNITIVE_OVERCONFIDENCE_PROMPT.format(
                self_knowledge_inflation=self_knowledge_inflation,
                introspection_overconfidence=introspection_overconfidence or "Not specified",
                monitoring_overconfidence=monitoring_overconfidence or "Not specified",
                correction_overconfidence=correction_overconfidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_METACOGNITIVE_OVERCONFIDENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_knowledge_inflation": self_knowledge_inflation[:200],
            "metacognitive_overconfidence_detected": data.get("metacognitive_overconfidence_detected", False),
            "severity": data.get("severity", ""),
            "introspection_overconfidence": data.get("introspection_overconfidence", ""),
            "monitoring_overconfidence": data.get("monitoring_overconfidence", ""),
            "correction_overconfidence": data.get("correction_overconfidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
