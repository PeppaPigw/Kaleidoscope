"""EpistemicDigitalContextCollapseService — Epistemic Digital Context Collapse Detection.

Detects epistemic digital context collapse — context collapse making messages
reach unintended audiences who lack necessary context for interpretation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIGITAL_CONTEXT_COLLAPSE_SYSTEM = """You are an epistemic digital context collapse specialist. Given context collapse, assess misinterpretation risk:

Key concepts:
- Epistemic digital context collapse: messages reaching unintended audiences
- Audience mismatch: content designed for one audience reaching another
- Jargon misinterpretation: specialized language misunderstood by general audience
- Tone loss: tone and intent lost in decontextualized sharing
- Screenshot culture: decontextualized screenshots spreading
- Quote mining: quotes removed from context
- Viral decontextualization: viral spread stripping context

When epistemic digital context collapse IS present:
- Messages reaching unintended audiences
- Audience mismatch occurring
- Jargon misinterpreted
- Tone lost
- Screenshots decontextualized
- Quotes mined
- Viral spread stripping context

When no context collapse:
- Audiences appropriate
- Context preserved
- Jargon explained
- Tone maintained
- Full context shared
- Quotes in context
- Sharing preserves meaning

Output JSON with: context_collapse_detected (bool), severity (none/mild/moderate/severe), audience_mismatch (what audience mismatch), tone_loss (what tone lost), screenshot_decontextualization (what screenshots decontextualized), viral_decontextualization (what viral decontextualization), recommendation (no_context_collapse/mild_context_awareness/significant_audience_consideration/major_intensive_context_preservation/emergency_complete_context_collapse)."""

EPISTEMIC_DIGITAL_CONTEXT_COLLAPSE_PROMPT = """Detect epistemic digital context collapse:

Audience mismatch: {audience_mismatch}
Tone loss: {tone_loss}
Screenshot decontextualization: {screenshot_decontextualization}
Viral decontextualization: {viral_decontextualization}
Domain: {domain}
Context: {context}

Is context collapse making messages reach unintended audiences? Return ONLY valid JSON."""


class EpistemicDigitalContextCollapseService:
    """Detects epistemic digital context collapse — audience mismatch."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        audience_mismatch: str,
        *,
        tone_loss: str = "",
        screenshot_decontextualization: str = "",
        viral_decontextualization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic digital context collapse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIGITAL_CONTEXT_COLLAPSE_PROMPT.format(
                audience_mismatch=audience_mismatch,
                tone_loss=tone_loss or "Not specified",
                screenshot_decontextualization=screenshot_decontextualization or "Not specified",
                viral_decontextualization=viral_decontextualization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIGITAL_CONTEXT_COLLAPSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "audience_mismatch": audience_mismatch[:200],
            "context_collapse_detected": data.get("context_collapse_detected", False),
            "severity": data.get("severity", ""),
            "tone_loss": data.get("tone_loss", ""),
            "screenshot_decontextualization": data.get("screenshot_decontextualization", ""),
            "viral_decontextualization": data.get("viral_decontextualization", ""),
            "recommendation": data.get("recommendation", ""),
        }
