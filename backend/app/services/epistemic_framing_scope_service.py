"""EpistemicFramingScopeService — Epistemic Scope Framing Detection.

Detects epistemic framing scope manipulation — framing scope to strategically
include or exclude information that changes interpretation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FRAMING_SCOPE_SYSTEM = """You are an epistemic framing scope specialist. Given scope framing, assess strategic inclusion/exclusion:

Key concepts:
- Epistemic scope framing: strategic scope to include/exclude information
- Narrow framing: narrowing scope to exclude inconvenient context
- Broad framing: broadening scope to dilute specific findings
- Boundary gerrymandering: drawing boundaries to include/exclude strategically
- System boundary manipulation: defining system boundaries to change conclusions
- Comparison scope: choosing comparison scope to favor desired conclusion
- Temporal scope manipulation: choosing time window to support narrative

When epistemic scope framing IS present:
- Scope strategically chosen
- Narrow framing excluding context
- Broad framing diluting findings
- Boundaries gerrymandered
- System boundaries manipulated
- Comparison scope biased
- Temporal scope manipulated

When no scope framing:
- Scope appropriate and justified
- Context included
- Findings not diluted
- Boundaries natural
- System boundaries appropriate
- Comparisons fair
- Time windows justified

Output JSON with: scope_framing_detected (bool), severity (none/mild/moderate/severe), narrow_framing (what narrowed), broad_framing (what broadened), boundary_gerrymandering (what boundaries gerrymandered), temporal_scope_manipulation (what temporal scope manipulated), recommendation (no_scope_framing/mild_scope_justification/significant_scope_expansion/major_intensive_boundary_audit/emergency_complete_scope_manipulation)."""

EPISTEMIC_FRAMING_SCOPE_PROMPT = """Detect epistemic scope framing manipulation:

Narrow framing: {narrow_framing}
Broad framing: {broad_framing}
Boundary gerrymandering: {boundary_gerrymandering}
Temporal scope manipulation: {temporal_scope_manipulation}
Domain: {domain}
Context: {context}

Is scope being framed to strategically include or exclude information? Return ONLY valid JSON."""


class EpistemicFramingScopeService:
    """Detects epistemic scope framing — strategic inclusion/exclusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrow_framing: str,
        *,
        broad_framing: str = "",
        boundary_gerrymandering: str = "",
        temporal_scope_manipulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scope framing manipulation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FRAMING_SCOPE_PROMPT.format(
                narrow_framing=narrow_framing,
                broad_framing=broad_framing or "Not specified",
                boundary_gerrymandering=boundary_gerrymandering or "Not specified",
                temporal_scope_manipulation=temporal_scope_manipulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FRAMING_SCOPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrow_framing": narrow_framing[:200],
            "scope_framing_detected": data.get("scope_framing_detected", False),
            "severity": data.get("severity", ""),
            "broad_framing": data.get("broad_framing", ""),
            "boundary_gerrymandering": data.get("boundary_gerrymandering", ""),
            "temporal_scope_manipulation": data.get("temporal_scope_manipulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
