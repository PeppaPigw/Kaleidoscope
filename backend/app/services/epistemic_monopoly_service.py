"""EpistemicMonopolyService — Epistemic Monopoly Detection.

Detects epistemic monopoly — single sources or frameworks
dominating knowledge production and distribution.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MONOPOLY_SYSTEM = """You are an epistemic monopoly specialist. Given a knowledge production landscape, assess whether single sources dominate:

Key concepts:
- Epistemic monopoly: single source dominating knowledge production
- Market dominance: one framework dominating the space
- Competition suppression: suppressing alternative viewpoints
- Barrier to entry: barriers preventing new knowledge producers
- Network effects: dominance reinforced by network effects
- Lock-in: audiences locked into single source
- Innovation suppression: monopoly suppressing innovation

When epistemic monopoly IS present:
- Single source dominating knowledge production
- One framework dominating to exclusion of others
- Alternative viewpoints suppressed
- Barriers preventing new knowledge producers
- Dominance reinforced by network effects
- Audiences locked into single source
- Innovation suppressed by dominant position

When healthy competition is present:
- Multiple sources contributing knowledge
- Multiple frameworks coexisting
- Alternative viewpoints welcomed
- Low barriers to new knowledge production
- Merit-based rather than network-effect-based success
- Audiences free to choose sources
- Innovation encouraged by competition

Output JSON with: monopoly_present (bool), severity (none/mild/moderate/severe), source (what source dominates), market (what market is monopolized), suppression (what is suppressed), barriers (what barriers exist), recommendation (healthy_competition/mild_dominance/significant_monopoly/major_market_capture/restore_competition)."""

EPISTEMIC_MONOPOLY_PROMPT = """Detect epistemic monopoly:

Source: {source}
Market: {market}
Suppression: {suppression}
Barriers: {barriers}
Domain: {domain}
Context: {context}

Is a single source or framework dominating knowledge production? Return ONLY valid JSON."""


class EpistemicMonopolyService:
    """Detects epistemic monopoly — single sources dominating knowledge production."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        source: str,
        *,
        market: str = "",
        suppression: str = "",
        barriers: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic monopoly."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MONOPOLY_PROMPT.format(
                source=source,
                market=market or "Not specified",
                suppression=suppression or "Not specified",
                barriers=barriers or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MONOPOLY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "source": source[:200],
            "monopoly_present": data.get("monopoly_present", False),
            "severity": data.get("severity", ""),
            "market": data.get("market", ""),
            "suppression": data.get("suppression", ""),
            "barriers": data.get("barriers", ""),
            "recommendation": data.get("recommendation", ""),
        }
