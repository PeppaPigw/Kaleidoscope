"""EpistemicMemorySourceConfusionService — Epistemic Memory Source Confusion Detection.

Detects epistemic memory source confusion — confusing where information was
learned, attributing it to wrong sources.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_SOURCE_CONFUSION_SYSTEM = """You are an epistemic memory source confusion specialist. Given source confusion, assess misattribution:

Key concepts:
- Epistemic memory source confusion: confusing where information was learned
- Source misattribution: attributing information to wrong source
- Reality monitoring failure: confusing imagined with experienced
- Cryptomnesia: forgetting source, treating as original thought
- Authority source inflation: misremembering source as more authoritative
- Temporal source confusion: confusing when information was learned
- Context source stripping: remembering fact but losing source context

When epistemic memory source confusion IS present:
- Sources confused or misattributed
- Reality monitoring failing
- Cryptomnesia operating
- Authority sources inflated
- Temporal sources confused
- Context stripped from sources
- Original sources lost

When no source confusion:
- Sources accurately tracked
- Reality monitoring intact
- Original sources acknowledged
- Authority accurately attributed
- Temporal context preserved
- Source context maintained
- Provenance clear

Output JSON with: source_confusion_detected (bool), severity (none/mild/moderate/severe), source_misattribution (what misattributed), reality_monitoring_failure (what reality monitoring failing), cryptomnesia (what cryptomnesia), authority_source_inflation (what authority inflated), recommendation (no_source_confusion/mild_source_checking/significant_provenance_tracking/major_intensive_source_verification/emergency_complete_source_confusion)."""

EPISTEMIC_MEMORY_SOURCE_CONFUSION_PROMPT = """Detect epistemic memory source confusion:

Source misattribution: {source_misattribution}
Reality monitoring failure: {reality_monitoring_failure}
Cryptomnesia: {cryptomnesia}
Authority source inflation: {authority_source_inflation}
Domain: {domain}
Context: {context}

Is the source of information being confused or misattributed? Return ONLY valid JSON."""


class EpistemicMemorySourceConfusionService:
    """Detects epistemic memory source confusion — source misattribution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source_misattribution: str,
        *,
        reality_monitoring_failure: str = "",
        cryptomnesia: str = "",
        authority_source_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory source confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_SOURCE_CONFUSION_PROMPT.format(
                source_misattribution=source_misattribution,
                reality_monitoring_failure=reality_monitoring_failure or "Not specified",
                cryptomnesia=cryptomnesia or "Not specified",
                authority_source_inflation=authority_source_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_SOURCE_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source_misattribution": source_misattribution[:200],
            "source_confusion_detected": data.get("source_confusion_detected", False),
            "severity": data.get("severity", ""),
            "reality_monitoring_failure": data.get("reality_monitoring_failure", ""),
            "cryptomnesia": data.get("cryptomnesia", ""),
            "authority_source_inflation": data.get("authority_source_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
