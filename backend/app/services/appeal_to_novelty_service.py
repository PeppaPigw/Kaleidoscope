"""AppealToNoveltyService — Appeal to Novelty Detection.

Detects appeal to novelty (argumentum ad novitatem) — arguing
that something is better or more correct simply because it is
new, modern, or recent. The mirror image of appeal to tradition.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

APPEAL_NOVELTY_SYSTEM = """You are an appeal to novelty specialist. Given an argument, assess whether it fallaciously equates 'new' or 'modern' with 'better' or 'correct':

Key concepts:
- Argumentum ad novitatem: new = better fallacy
- Chronological snobbery: dismissing old ideas merely for being old
- Progress narrative: assuming all change is improvement
- Novelty bias: preferring new things without evaluating merit
- Innovation fetishism: treating newness as inherently valuable
- Planned obsolescence: manufactured perception that old = inferior
- Genuine improvement: sometimes new IS better (distinguish from fallacy)

When appeal to novelty IS present:
- "This is the latest approach, so it must be better"
- Dismissing established methods solely for being old
- "That's outdated thinking" without explaining why it's wrong
- Treating newness as self-justifying
- "Move with the times" as sole argument
- Marketing newness as proof of superiority
- Assuming newer technology/methods are always improvements

When appeal to novelty is NOT present:
- New approach has demonstrated advantages over old
- Specific improvements are identified and evidenced
- Acknowledging that newness alone doesn't guarantee quality
- Empirical comparison between old and new approaches
- New method addresses known limitations of the old
- Innovation evaluated on its merits, not just its recency
- Context where newer information genuinely supersedes older

Output JSON with: appeal_to_novelty_present (bool), severity (none/mild/moderate/severe), claim (what is argued), novelty_cited (what newness is invoked), demonstrated_improvement (is there evidence the new is actually better), old_dismissed (what established approach is dismissed), recommendation (no_appeal_to_novelty/mild_novelty_bias/significant_appeal_to_novelty/major_chronological_snobbery/evaluate_on_merits)."""

APPEAL_NOVELTY_PROMPT = """Detect appeal to novelty:

Argument: {argument}
New thing cited: {novelty}
Claimed improvement: {improvement}
What is dismissed: {dismissed}
Domain: {domain}
Context: {context}

Does this argue something is better merely because it's new? Return ONLY valid JSON."""


class AppealToNoveltyService:
    """Detects appeal to novelty — equating new/modern with better."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        novelty: str = "",
        improvement: str = "",
        dismissed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect appeal to novelty."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=APPEAL_NOVELTY_PROMPT.format(
                argument=argument,
                novelty=novelty or "Not specified",
                improvement=improvement or "Not specified",
                dismissed=dismissed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=APPEAL_NOVELTY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "appeal_to_novelty_present": data.get("appeal_to_novelty_present", False),
            "severity": data.get("severity", ""),
            "novelty_cited": data.get("novelty_cited", ""),
            "demonstrated_improvement": data.get("demonstrated_improvement", ""),
            "old_dismissed": data.get("old_dismissed", ""),
            "recommendation": data.get("recommendation", ""),
        }
