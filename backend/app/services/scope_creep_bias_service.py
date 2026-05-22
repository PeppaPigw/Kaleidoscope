"""ScopeCreepBiasService — Scope Creep Bias Detection.

Detects scope creep bias — the gradual, unnoticed expansion of
project scope, requirements, or commitments beyond original
boundaries. Each individual addition seems small and reasonable,
but the cumulative effect transforms the project. The boiling
frog of project management — no single change triggers alarm,
but the total drift is massive.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCOPE_CREEP_BIAS_SYSTEM = """You are a scope creep bias specialist. Given a project or commitment situation, assess whether gradual scope expansion is occurring unnoticed:

Key concepts:
- Scope creep: gradual expansion beyond original boundaries
- Salami tactics: thin slices of addition that individually seem harmless
- Commitment escalation interaction: each addition makes next easier to justify
- Boiling frog: no single change triggers alarm
- Feature creep: adding capabilities beyond original requirements
- Requirements drift: specifications expanding without formal change
- Gold plating: adding unrequested improvements

When scope creep bias IS present:
- "While we're at it, let's also..." pattern
- Original scope unrecognizable but no formal change was made
- Each addition justified individually but total is unjustifiable
- "It's just a small addition" repeated many times
- No one tracking cumulative scope changes
- Timeline/budget unchanged despite expanded scope
- "We might as well" reasoning for additions

When scope expansion IS appropriate:
- Formal change control process is followed
- Resources are adjusted to match expanded scope
- The expansion is explicitly acknowledged and approved
- Original scope was genuinely insufficient for the goal
- Stakeholders are informed of cumulative changes
- Trade-offs are explicitly made (add X, remove Y)

Output JSON with: scope_creep_present (bool), severity (none/mild/moderate/severe), project (what project or commitment), original_scope (what was the original scope), current_scope (what is the current scope), drift_mechanism (how did scope expand), individual_additions (what individual additions occurred), cumulative_impact (what is the total impact), resource_adjustment (were resources adjusted), recommendation (expansion_managed/mild_scope_drift/significant_scope_creep/major_uncontrolled_expansion/implement_change_control)."""

SCOPE_CREEP_BIAS_PROMPT = """Detect scope creep bias:

Project: {project}
Original scope: {original}
Current state: {current}
Additions: {additions}
Domain: {domain}
Context: {context}

Is scope gradually expanding without formal acknowledgment or resource adjustment? Return ONLY valid JSON."""


class ScopeCreepBiasService:
    """Detects scope creep bias — gradual unnoticed scope expansion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        project: str,
        *,
        original: str = "",
        current: str = "",
        additions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect scope creep bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCOPE_CREEP_BIAS_PROMPT.format(
                project=project,
                original=original or "Not specified",
                current=current or "Not specified",
                additions=additions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SCOPE_CREEP_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "project": project[:200],
            "scope_creep_present": data.get("scope_creep_present", False),
            "severity": data.get("severity", ""),
            "original_scope": data.get("original_scope", ""),
            "current_scope": data.get("current_scope", ""),
            "drift_mechanism": data.get("drift_mechanism", ""),
            "individual_additions": data.get("individual_additions", ""),
            "cumulative_impact": data.get("cumulative_impact", ""),
            "resource_adjustment": data.get("resource_adjustment", ""),
            "recommendation": data.get("recommendation", ""),
        }
