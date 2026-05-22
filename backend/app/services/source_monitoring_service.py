"""SourceMonitoringService — Source Monitoring Error Detection.

Detects source monitoring errors — failure to correctly
attribute the origin of a memory, knowledge, or belief.
Johnson, Hashtroudi & Lindsay (1993). "Where did I learn
that?" Confusing imagination with reality, dreams with
events, or one source with another. Leads to false
confidence and misattributed knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SOURCE_MONITORING_SYSTEM = """You are a source monitoring specialist. Given a claim or belief, assess whether the person correctly identifies where the information came from:

Key concepts (Johnson, Hashtroudi & Lindsay, 1993):
- Source monitoring: attributing memories to their correct origin
- Reality monitoring: distinguishing internal (imagined) from external (perceived)
- Internal source confusion: confusing thought with action
- External source confusion: confusing one external source with another
- Sleeper effect: forgetting source while retaining content
- Unconscious plagiarism: generating ideas believed to be original
- Imagination inflation: imagining events increases belief they occurred

When source monitoring error IS present:
- "I read that somewhere" but can't identify where
- Confusing what was imagined/planned with what was done
- Attributing information to wrong source
- "I came up with that idea" when it was heard from someone else
- Treating rumors or speculation as established facts
- Confusing what was dreamed/imagined with what happened
- "Everyone knows that" without traceable source

When the attribution IS correct:
- The person can identify the specific source
- The memory includes contextual details of encoding
- Multiple sources confirm the same information
- The person distinguishes confidence from source certainty
- The attribution has been verified against records

Output JSON with: source_monitoring_error_present (bool), severity (none/mild/moderate/severe), claim (what is being claimed), attributed_source (where does the person think it came from), likely_source (where did it likely come from), confusion_type (reality/internal/external source confusion), verifiability (can the source be verified), confidence_source_mismatch (is confidence higher than source certainty warrants), recommendation (attribution_correct/mild_source_confusion/significant_misattribution/major_source_error/verify_original_source)."""

SOURCE_MONITORING_PROMPT = """Detect source monitoring error:

Claim: {claim}
Attribution: {attribution}
Evidence: {evidence}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is the person correctly identifying where this information came from? Return ONLY valid JSON."""


class SourceMonitoringService:
    """Detects source monitoring errors — misattributing the origin of knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        attribution: str = "",
        evidence: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect source monitoring error."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SOURCE_MONITORING_PROMPT.format(
                claim=claim,
                attribution=attribution or "Not specified",
                evidence=evidence or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SOURCE_MONITORING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "source_monitoring_error_present": data.get("source_monitoring_error_present", False),
            "severity": data.get("severity", ""),
            "attributed_source": data.get("attributed_source", ""),
            "likely_source": data.get("likely_source", ""),
            "confusion_type": data.get("confusion_type", ""),
            "verifiability": data.get("verifiability", ""),
            "confidence_source_mismatch": data.get("confidence_source_mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }
