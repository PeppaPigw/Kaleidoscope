"""ScissorStatementService — Scissor Statement Detection.

Detects scissor statements — statements specifically designed or
naturally occurring to maximally divide people along existing fault
lines. Scott Alexander (2018). A scissor statement splits any group
into two halves who each find the other's position not just wrong
but morally abhorrent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCISSOR_STATEMENT_SYSTEM = """You are a scissor statement specialist. Given a statement or framing, assess whether it is designed to maximally divide people along existing fault lines:

Key concepts (Scott Alexander, 2018):
- Scissor statement: maximally divides a group into opposing camps
- Moral valence inversion: each side sees the other as morally wrong
- Fault line exploitation: targets existing but dormant disagreements
- Engagement maximization: designed to provoke maximum response
- False dichotomy overlap: forces binary choice on complex issue
- Toxoplasma of rage overlap: controversial enough to spread, not resolve
- Outrage symmetry: both sides equally outraged by the other

When scissor statement IS present:
- A statement that splits any group roughly 50/50
- Each side finds the other's position morally incomprehensible
- The statement is simple but the disagreement is deep
- Discussion generates heat but no resolution
- People who agree on most things suddenly find themselves opposed
- The framing makes compromise seem like moral failure
- Designed to maximize engagement through division

When divisive statement is NOT a scissor:
- One side has clear majority (not a true split)
- The disagreement is intellectual, not moral
- Compromise positions are readily available
- The division maps to existing well-understood political lines
- The statement is genuinely important and division is unavoidable
- Discussion can actually resolve the disagreement
- The framing allows for nuance and middle ground

Output JSON with: scissor_present (bool), severity (none/mild/moderate/severe), statement (the statement analyzed), division (how it divides people), moral_valence (do both sides see the other as morally wrong), resolution_possible (can this be resolved through discussion), engagement_pattern (does it maximize engagement), recommendation (legitimate_disagreement/mild_divisiveness/significant_scissor/major_fault_line_exploit/reframe_to_allow_nuance)."""

SCISSOR_STATEMENT_PROMPT = """Detect scissor statement:

Statement: {statement}
Division: {division}
Reactions: {reactions}
Resolution: {resolution}
Domain: {domain}
Context: {context}

Is this statement designed to maximally divide people along existing fault lines? Return ONLY valid JSON."""


class ScissorStatementService:
    """Detects scissor statements — maximally divisive framings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        statement: str,
        *,
        division: str = "",
        reactions: str = "",
        resolution: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scissor statement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCISSOR_STATEMENT_PROMPT.format(
                statement=statement,
                division=division or "Not specified",
                reactions=reactions or "Not specified",
                resolution=resolution or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCISSOR_STATEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "statement": statement[:200],
            "scissor_present": data.get("scissor_present", False),
            "severity": data.get("severity", ""),
            "division": data.get("division", ""),
            "moral_valence": data.get("moral_valence", ""),
            "resolution_possible": data.get("resolution_possible", ""),
            "engagement_pattern": data.get("engagement_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
