"""OptionFramingService — Option Framing Detection.

Detects option framing bias — when how options are described
(rather than their actual properties) biases selection. The
same option described differently can be chosen or rejected
based purely on framing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OPTION_FRAMING_SYSTEM = """You are an option framing specialist. Given a set of options, assess whether their descriptions bias selection:

Key concepts:
- Option framing: how description influences choice
- Gain vs loss framing: same outcome described as gain or loss
- Attribute framing: emphasizing different attributes of same option
- Goal framing: framing in terms of achieving vs avoiding
- Risky choice framing: certainty vs probability framing
- Label effects: names and labels influencing perception
- Evaluability: how easy it is to assess each option

When option framing IS biasing:
- Same option would be chosen/rejected based on description alone
- Gain framing for favored option, loss framing for disfavored
- Positive attributes highlighted for one, negative for another
- Labels creating positive/negative associations
- Description complexity differs between options
- Emotional language used asymmetrically
- Framing would change choice if reversed

When option framing is neutral:
- Options described in comparable terms
- Same frame applied to all options
- Both positive and negative attributes mentioned for each
- Labels are neutral and descriptive
- Complexity of description is similar across options
- Emotional tone is consistent
- Choice would be same regardless of which frame is used

Output JSON with: framing_bias (bool), severity (none/mild/moderate/severe), options (what options are presented), framing_technique (how framing differs between options), reversal_test (would choice change if framing reversed), asymmetry (how descriptions differ), recommendation (neutral_framing/mild_asymmetry/significant_framing_bias/major_manipulation/equalize_descriptions)."""

OPTION_FRAMING_PROMPT = """Detect option framing bias:

Options presented: {options}
Descriptions: {descriptions}
Favored option: {favored}
Framing used: {framing}
Domain: {domain}
Context: {context}

Are option descriptions biasing selection? Return ONLY valid JSON."""


class OptionFramingService:
    """Detects option framing — descriptions biasing selection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        options: str,
        *,
        descriptions: str = "",
        favored: str = "",
        framing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect option framing bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OPTION_FRAMING_PROMPT.format(
                options=options,
                descriptions=descriptions or "Not specified",
                favored=favored or "Not specified",
                framing=framing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OPTION_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "options": options[:200],
            "framing_bias": data.get("framing_bias", False),
            "severity": data.get("severity", ""),
            "framing_technique": data.get("framing_technique", ""),
            "reversal_test": data.get("reversal_test", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
