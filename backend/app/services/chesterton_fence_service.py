"""ChestertonFenceService — Chesterton's Fence Analysis.

Before removing something that seems pointless, understand why it was
put there. Identifies hidden functions, historical reasons, and
non-obvious purposes of existing structures, rules, or practices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHESTERTON_SYSTEM = """You are a Chesterton's Fence analyst. Given something that seems pointless or ready for removal, investigate why it exists:
- What problem did it originally solve?
- Does that problem still exist (even if not visible)?
- What hidden functions does it serve beyond the obvious?
- Who benefits from it in ways that aren't immediately apparent?
- What would break if it were removed?

Output JSON with: original_purpose (why it was created), original_problem (what problem it solved), problem_still_exists (bool), hidden_functions (list of: function, who_benefits, visibility (obvious/subtle/invisible)), removal_risks (list of: risk, severity (minor/moderate/major/catastrophic), likelihood (0-1)), lindy_effect (how long has it survived — longer survival suggests hidden value), previous_removal_attempts (what happened when similar things were removed), dependencies (what else relies on this existing), cultural_memory_lost (knowledge about why it exists that has been forgotten), safe_to_remove (bool), conditions_for_safe_removal (what must be true before removing), recommended_approach (remove/modify/keep/investigate_further), investigation_needed (what to check before deciding)."""

CHESTERTON_PROMPT = """Apply Chesterton's Fence:

Thing that seems pointless: {thing}
Why it seems removable: {why_remove}
Domain: {domain}
Context: {context}
How long it's existed: {age}

Why might this exist? Return ONLY valid JSON."""


class ChestertonFenceService:
    """Applies Chesterton's Fence analysis before removal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        thing: str,
        *,
        why_remove: str = "",
        domain: str = "",
        context: str = "",
        age: str = "",
    ) -> dict:
        """Analyze via Chesterton's Fence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHESTERTON_PROMPT.format(
                thing=thing,
                why_remove=why_remove or "Seems unnecessary",
                domain=domain or "general",
                context=context or "No additional context",
                age=age or "Unknown",
            ),
            system=CHESTERTON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "thing": thing[:200],
            "original_purpose": data.get("original_purpose", ""),
            "original_problem": data.get("original_problem", ""),
            "problem_still_exists": data.get("problem_still_exists", True),
            "hidden_functions": data.get("hidden_functions", []),
            "removal_risks": data.get("removal_risks", []),
            "lindy_effect": data.get("lindy_effect", ""),
            "previous_removal_attempts": data.get("previous_removal_attempts", ""),
            "dependencies": data.get("dependencies", []),
            "cultural_memory_lost": data.get("cultural_memory_lost", ""),
            "safe_to_remove": data.get("safe_to_remove", False),
            "conditions_for_safe_removal": data.get("conditions_for_safe_removal", ""),
            "recommended_approach": data.get("recommended_approach", ""),
            "investigation_needed": data.get("investigation_needed", ""),
        }
