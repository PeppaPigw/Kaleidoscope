"""ExplanationDepthService — Multi-Level Explanation Generator.

Generates explanations at different levels of depth for the same finding.
Allows the research agent to match its communication to the audience:
from ELI5 through expert-level technical detail.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPLAIN_SYSTEM = """You are an explanation specialist. Given a research finding, generate explanations at multiple depth levels. Each level should be:
- Accurate (no oversimplification that introduces errors)
- Complete for its level (covers what that audience needs)
- Appropriately jargon-calibrated
- Useful (the reader can act on it)

Levels:
- eli5: A curious 5-year-old could understand. Analogies, no jargon.
- general: Educated non-specialist. Key concepts explained.
- undergraduate: Someone studying the field. Technical terms with brief definitions.
- graduate: Active researcher. Full technical detail, assumes domain knowledge.
- expert: Leading researcher. Nuances, limitations, connections to cutting edge.

Output JSON with: explanations.eli5 (2-3 sentences), explanations.general (1 paragraph), explanations.undergraduate (2 paragraphs), explanations.graduate (technical explanation), explanations.expert (nuanced expert-level), key_insight (the one thing everyone should understand regardless of level), common_misunderstandings (list of things people get wrong at each level)."""

EXPLAIN_PROMPT = """Generate multi-level explanations for this finding:

Finding: {finding}
Domain: {domain}
Target levels: {levels}

Explain at each level. Return ONLY valid JSON."""


class ExplanationDepthService:
    """Generates explanations at multiple depth levels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def explain(
        self,
        finding: str,
        *,
        levels: list[str] | None = None,
        domain: str = "",
    ) -> dict:
        """Generate explanations at multiple depth levels."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        target_levels = levels or ["eli5", "general", "undergraduate", "graduate", "expert"]

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPLAIN_PROMPT.format(
                finding=finding,
                domain=domain or "research",
                levels=", ".join(target_levels),
            ),
            system=EXPLAIN_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        explanations = data.get("explanations", data)

        return {
            "finding": finding[:200],
            "explanations": {k: v for k, v in explanations.items() if k in target_levels},
            "key_insight": data.get("key_insight", ""),
            "common_misunderstandings": data.get("common_misunderstandings", []),
        }
