"""EpistemicDementiaService — Epistemic Dementia Detection.

Detects epistemic dementia — progressive decline in intellectual function
affecting memory, reasoning, and daily cognitive operations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEMENTIA_SYSTEM = """You are an epistemic dementia specialist. Given progressive intellectual decline, assess dementia:

Key concepts:
- Epistemic dementia: progressive intellectual function decline
- Memory loss: inability to retain new intellectual content
- Executive dysfunction: inability to plan and organize
- Aphasia: loss of intellectual language ability
- Agnosia: inability to recognize intellectual objects
- Apraxia: inability to perform intellectual tasks
- Sundowning: worsening function at certain times

When epistemic dementia IS present:
- Progressive intellectual decline occurring
- Cannot retain new content
- Cannot plan or organize
- Losing language ability
- Cannot recognize familiar concepts
- Cannot perform familiar tasks
- Function worsening at certain times

When no dementia:
- Stable intellectual function
- Normal retention
- Normal planning ability
- Language intact
- Recognition normal
- Task performance normal
- Consistent function

Output JSON with: dementia_detected (bool), severity (none/mild/moderate/severe), memory_status (what retention), executive_function (what planning ability), language_status (what communication), recognition_status (what identification), recommendation (no_dementia/mild_cognitive_impairment/significant_early_dementia/major_moderate_dementia/advanced_severe_dementia)."""

EPISTEMIC_DEMENTIA_PROMPT = """Detect epistemic dementia:

Memory status: {memory_status}
Executive function: {executive_function}
Language status: {language_status}
Recognition status: {recognition_status}
Domain: {domain}
Context: {context}

Is there progressive decline in intellectual function? Return ONLY valid JSON."""


class EpistemicDementiaService:
    """Detects epistemic dementia — progressive intellectual function decline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        memory_status: str,
        *,
        executive_function: str = "",
        language_status: str = "",
        recognition_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dementia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEMENTIA_PROMPT.format(
                memory_status=memory_status,
                executive_function=executive_function or "Not specified",
                language_status=language_status or "Not specified",
                recognition_status=recognition_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEMENTIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "memory_status": memory_status[:200],
            "dementia_detected": data.get("dementia_detected", False),
            "severity": data.get("severity", ""),
            "executive_function": data.get("executive_function", ""),
            "language_status": data.get("language_status", ""),
            "recognition_status": data.get("recognition_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
