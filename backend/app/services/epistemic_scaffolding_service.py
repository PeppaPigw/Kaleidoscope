"""EpistemicScaffoldingService — Epistemic Scaffolding Detection.

Detects epistemic scaffolding — temporary supports that have become
permanent without being designed for long-term load.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCAFFOLDING_SYSTEM = """You are an epistemic scaffolding specialist. Given a knowledge structure, assess whether temporary supports have become permanent:

Key concepts:
- Epistemic scaffolding: temporary supports become permanent
- Temporary permanence: temporary measures lasting indefinitely
- Design mismatch: supports not designed for permanent load
- Removal failure: failure to remove scaffolding when no longer needed
- Hidden dependency: dependency on scaffolding not recognized
- Structural confusion: confusion between scaffolding and structure
- Technical debt analog: intellectual technical debt from scaffolding

When epistemic scaffolding IS present:
- Temporary supports have become permanent
- Temporary measures lasting indefinitely
- Supports not designed for the load they now bear
- Scaffolding not removed when no longer needed
- Dependency on scaffolding not recognized
- Confusion between scaffolding and actual structure
- Intellectual technical debt accumulating

When appropriate support is present:
- Supports designed for their current role
- Temporary measures removed when no longer needed
- Supports appropriate for their load
- Clear distinction between temporary and permanent
- Dependencies recognized and managed
- Structure and support clearly distinguished
- No unnecessary technical debt

Output JSON with: scaffolding_present (bool), severity (none/mild/moderate/severe), structure (what structure exists), scaffolding (what scaffolding remains), original_purpose (what it was designed for), current_load (what load it now bears), recommendation (appropriate_support/mild_permanence/significant_scaffolding/major_structural_confusion/replace_with_proper_structure)."""

EPISTEMIC_SCAFFOLDING_PROMPT = """Detect epistemic scaffolding:

Structure: {structure}
Scaffolding: {scaffolding}
Original purpose: {original_purpose}
Current load: {current_load}
Domain: {domain}
Context: {context}

Have temporary supports become permanent without being designed for it? Return ONLY valid JSON."""


class EpistemicScaffoldingService:
    """Detects epistemic scaffolding — temporary supports become permanent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        scaffolding: str = "",
        original_purpose: str = "",
        current_load: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scaffolding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCAFFOLDING_PROMPT.format(
                structure=structure,
                scaffolding=scaffolding or "Not specified",
                original_purpose=original_purpose or "Not specified",
                current_load=current_load or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCAFFOLDING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "scaffolding_present": data.get("scaffolding_present", False),
            "severity": data.get("severity", ""),
            "scaffolding": data.get("scaffolding", ""),
            "original_purpose": data.get("original_purpose", ""),
            "current_load": data.get("current_load", ""),
            "recommendation": data.get("recommendation", ""),
        }
