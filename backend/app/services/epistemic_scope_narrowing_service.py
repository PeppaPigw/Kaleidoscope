"""EpistemicScopeNarrowingService — Epistemic Scope Narrowing Detection.

Detects epistemic scope narrowing — artificially narrowing the scope
of inquiry to avoid uncomfortable conclusions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCOPE_NARROWING_SYSTEM = """You are an epistemic scope narrowing specialist. Given artificial narrowing of inquiry scope, assess scope narrowing:

Key concepts:
- Epistemic scope narrowing: artificially narrowing scope to avoid conclusions
- Convenient boundaries: drawing boundaries that exclude inconvenient evidence
- Cherry-picked scope: scope chosen to support preferred conclusion
- Exclusion strategy: strategically excluding relevant considerations
- Tunnel vision by design: deliberately creating tunnel vision
- Relevance manipulation: manipulating what counts as relevant
- Context stripping: stripping context that would change conclusions

When epistemic scope narrowing IS present:
- Scope artificially narrowed
- Boundaries conveniently drawn
- Scope cherry-picked
- Relevant considerations excluded
- Tunnel vision deliberate
- Relevance manipulated
- Context stripped

When no scope narrowing:
- Scope appropriate to question
- Boundaries principled
- Scope comprehensive
- All relevant considerations included
- Vision appropriately broad
- Relevance honestly assessed
- Context preserved

Output JSON with: scope_narrowing_detected (bool), severity (none/mild/moderate/severe), convenient_boundaries (what boundaries convenient), exclusion_strategy (what excluded), relevance_manipulation (what relevance manipulated), context_stripping (what context stripped), recommendation (no_scope_narrowing/mild_scope_expansion/significant_boundary_review/major_intensive_scope_correction/emergency_complete_scope_narrowing)."""

EPISTEMIC_SCOPE_NARROWING_PROMPT = """Detect epistemic scope narrowing:

Convenient boundaries: {convenient_boundaries}
Exclusion strategy: {exclusion_strategy}
Relevance manipulation: {relevance_manipulation}
Context stripping: {context_stripping}
Domain: {domain}
Context: {context}

Is scope being artificially narrowed to avoid uncomfortable conclusions? Return ONLY valid JSON."""


class EpistemicScopeNarrowingService:
    """Detects epistemic scope narrowing — artificial boundary drawing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        convenient_boundaries: str,
        *,
        exclusion_strategy: str = "",
        relevance_manipulation: str = "",
        context_stripping: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scope narrowing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCOPE_NARROWING_PROMPT.format(
                convenient_boundaries=convenient_boundaries,
                exclusion_strategy=exclusion_strategy or "Not specified",
                relevance_manipulation=relevance_manipulation or "Not specified",
                context_stripping=context_stripping or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCOPE_NARROWING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "convenient_boundaries": convenient_boundaries[:200],
            "scope_narrowing_detected": data.get("scope_narrowing_detected", False),
            "severity": data.get("severity", ""),
            "exclusion_strategy": data.get("exclusion_strategy", ""),
            "relevance_manipulation": data.get("relevance_manipulation", ""),
            "context_stripping": data.get("context_stripping", ""),
            "recommendation": data.get("recommendation", ""),
        }
