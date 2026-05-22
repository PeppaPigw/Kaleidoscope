"""ArgumentStrengthRankerService — Evidence-Based Argument Ranking.

Ranks arguments by actual evidential strength rather than rhetorical
persuasiveness. Separates strong evidence from compelling rhetoric,
identifying which arguments should actually move your beliefs vs which
just sound convincing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

RANK_SYSTEM = """You are an argument strength analyst. Given multiple arguments about a position, rank them by EVIDENTIAL strength (not rhetorical persuasiveness). For each argument assess:
- Evidence quality: is it backed by strong empirical evidence?
- Logical validity: is the reasoning sound?
- Relevance: does it actually bear on the conclusion?
- Independence: does it provide new information or just restate others?
- Robustness: would it survive scrutiny and counterargument?

Distinguish between:
- Strong evidence that sounds boring vs weak evidence that sounds compelling
- Arguments that should move beliefs vs arguments that just feel persuasive
- Novel information vs repackaged common knowledge

Output JSON with: ranked_arguments (list sorted by strength, each with: argument, evidential_strength (0-1), rhetorical_strength (0-1), gap (difference between how persuasive it sounds vs how strong it actually is), evidence_type, logical_validity (0-1), independence (0-1), verdict (strong/moderate/weak/misleading)), strongest_argument (which and why), most_overrated (sounds strong but isn't), most_underrated (sounds weak but is actually strong), overall_case_strength (0-1, how strong is the total body of arguments)."""

RANK_PROMPT = """Rank these arguments by evidential strength:

Position: {position}
Arguments:
{arguments_text}

Domain: {domain}

Rank by actual evidence quality, not persuasiveness. Return ONLY valid JSON."""


class ArgumentStrengthRankerService:
    """Ranks arguments by evidential strength, not rhetoric."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def rank_arguments(
        self,
        position: str,
        arguments: list[str],
        *,
        domain: str = "",
    ) -> dict:
        """Rank arguments by evidential strength."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        arguments_text = "\n".join(f"{i+1}. {a}" for i, a in enumerate(arguments[:10]))

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RANK_PROMPT.format(
                position=position,
                arguments_text=arguments_text,
                domain=domain or "general",
            ),
            system=RANK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        ranked = data.get("ranked_arguments", [])
        return {
            "position": position[:200],
            "arguments_ranked": len(ranked),
            "ranked": ranked,
            "strongest": data.get("strongest_argument", ""),
            "most_overrated": data.get("most_overrated", ""),
            "most_underrated": data.get("most_underrated", ""),
            "overall_case_strength": data.get("overall_case_strength", 0),
        }
