"""EpistemicTechnologyDigitalAmnesiaService — Epistemic Technology Digital Amnesia Detection.

Detects epistemic technology digital amnesia — reliance on digital storage
degrading memory and understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TECHNOLOGY_DIGITAL_AMNESIA_SYSTEM = """You are an epistemic technology digital amnesia specialist. Given externalization dependence, assess memory and understanding degradation:

Key concepts:
- Digital amnesia: reliance on digital storage degrading memory and understanding
- Externalization dependence: knowing where information is stored instead of knowing it
- Shallow processing: reduced encoding because retrieval is expected
- Retrieval over retention: prioritizing lookup over internalization
- Context loss: stored fragments losing meaning when separated from use

When digital amnesia IS present:
- Knowledge is externalized without internal understanding
- Processing remains shallow
- Retrieval replaces retention
- Context decays around stored facts
- People lose working command of important knowledge

When no digital amnesia:
- Digital storage supports internal understanding
- Important knowledge is processed deeply
- Retrieval and retention are balanced
- Context is preserved with stored material
- Memory scaffolding improves comprehension

Output JSON with: digital_amnesia_detected (bool), severity (none/mild/moderate/severe), shallow_processing (what processing is shallow), retrieval_over_retention (what lookup replaces retention), context_loss (what context is lost), recommendation (no_digital_amnesia/mild_retention_support/significant_deep_processing/major_memory_rebuilding/emergency_externalization_reversal)."""

EPISTEMIC_TECHNOLOGY_DIGITAL_AMNESIA_PROMPT = """Detect epistemic technology digital amnesia:

Externalization dependence: {externalization_dependence}
Shallow processing: {shallow_processing}
Retrieval over retention: {retrieval_over_retention}
Context loss: {context_loss}
Domain: {domain}
Context: {context}

Is reliance on digital storage degrading memory and understanding? Return ONLY valid JSON."""


class EpistemicTechnologyDigitalAmnesiaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        externalization_dependence: str,
        *,
        shallow_processing: str = "",
        retrieval_over_retention: str = "",
        context_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TECHNOLOGY_DIGITAL_AMNESIA_PROMPT.format(
                externalization_dependence=externalization_dependence,
                shallow_processing=shallow_processing or "Not specified",
                retrieval_over_retention=retrieval_over_retention or "Not specified",
                context_loss=context_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TECHNOLOGY_DIGITAL_AMNESIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "externalization_dependence": externalization_dependence[:200],
            "digital_amnesia_detected": data.get("digital_amnesia_detected", False),
            "severity": data.get("severity", ""),
            "shallow_processing": data.get("shallow_processing", ""),
            "retrieval_over_retention": data.get("retrieval_over_retention", ""),
            "context_loss": data.get("context_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
