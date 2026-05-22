"""EpistemicArbitrageService — Epistemic Arbitrage Detection.

Detects epistemic arbitrage — exploiting knowledge gaps between
communities for advantage rather than bridging them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ARBITRAGE_SYSTEM = """You are an epistemic arbitrage specialist. Given a knowledge gap pattern, assess whether gaps are exploited rather than bridged:

Key concepts:
- Epistemic arbitrage: exploiting knowledge gaps for advantage
- Gap exploitation: exploiting rather than bridging gaps
- Information asymmetry: using information asymmetry for gain
- Knowledge hoarding: hoarding knowledge for advantage
- Bridge refusal: refusing to bridge gaps to maintain advantage
- Middleman extraction: extracting value as knowledge middleman
- Deliberate opacity: maintaining opacity for advantage

When epistemic arbitrage IS present:
- Knowledge gaps exploited for advantage
- Gaps exploited rather than bridged
- Information asymmetry used for personal gain
- Knowledge hoarded to maintain advantage
- Refusing to bridge gaps to maintain position
- Extracting value as knowledge middleman
- Maintaining deliberate opacity for advantage

When knowledge bridging is present:
- Knowledge gaps bridged for mutual benefit
- Gaps addressed through sharing
- Information asymmetry reduced through education
- Knowledge shared freely
- Actively bridging gaps between communities
- Adding value through genuine translation
- Promoting transparency and understanding

Output JSON with: arbitrage_present (bool), severity (none/mild/moderate/severe), gap (what knowledge gap is exploited), exploiter (who exploits it), mechanism (how exploitation works), harm (what harm results), recommendation (knowledge_bridging/mild_exploitation/significant_arbitrage/major_gap_exploitation/bridge_the_gap)."""

EPISTEMIC_ARBITRAGE_PROMPT = """Detect epistemic arbitrage:

Gap: {gap}
Exploiter: {exploiter}
Mechanism: {mechanism}
Harm: {harm}
Domain: {domain}
Context: {context}

Are knowledge gaps being exploited for advantage rather than bridged? Return ONLY valid JSON."""


class EpistemicArbitrageService:
    """Detects epistemic arbitrage — exploiting knowledge gaps for advantage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gap: str,
        *,
        exploiter: str = "",
        mechanism: str = "",
        harm: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic arbitrage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ARBITRAGE_PROMPT.format(
                gap=gap,
                exploiter=exploiter or "Not specified",
                mechanism=mechanism or "Not specified",
                harm=harm or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ARBITRAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gap": gap[:200],
            "arbitrage_present": data.get("arbitrage_present", False),
            "severity": data.get("severity", ""),
            "exploiter": data.get("exploiter", ""),
            "mechanism": data.get("mechanism", ""),
            "harm": data.get("harm", ""),
            "recommendation": data.get("recommendation", ""),
        }
