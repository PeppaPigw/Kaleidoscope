"""SelectionEffectService — Selection Bias & Survivorship Detection.

Identifies selection effects that distort conclusions: survivorship bias,
publication bias, selection on the dependent variable, and other ways
the data we see is not representative of the full picture.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTION_SYSTEM = """You are a selection effect specialist. Given a claim and its evidence base, identify selection effects:
- Survivorship bias (we only see the winners/survivors)
- Publication bias (only positive results get published)
- Selection on dependent variable (only studying cases where the outcome occurred)
- Availability bias in evidence (we use what's easy to find, not what's representative)
- Self-selection (the sample chose to participate, creating bias)
- Attrition bias (who dropped out and why)

For each effect, assess how much it distorts the conclusion.

Output JSON with: selection_effects (list of: type (survivorship/publication/dependent_variable/availability/self_selection/attrition/other), description, severity (minor/moderate/major/invalidating), how_it_distorts (mechanism), corrected_estimate (what we'd conclude if we corrected for this)), overall_distortion (0-1, how much selection effects distort the conclusion), most_damaging_effect (which one matters most), what_we_dont_see (what's missing from the evidence because of selection), corrected_conclusion (what we'd conclude after accounting for all selection effects), data_needed_to_correct (what data would let us correct for these effects)."""

SELECTION_PROMPT = """Identify selection effects:

Claim: {claim}
Evidence base: {evidence}
How evidence was gathered: {method}
Domain: {domain}

What selection effects distort this? Return ONLY valid JSON."""


class SelectionEffectService:
    """Identifies selection effects that distort conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence: str = "",
        method: str = "",
        domain: str = "",
    ) -> dict:
        """Detect selection effects in evidence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTION_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                method=method or "Not specified",
                domain=domain or "general",
            ),
            system=SELECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        effects = data.get("selection_effects", [])
        return {
            "claim": claim[:200],
            "effects_count": len(effects),
            "selection_effects": effects,
            "overall_distortion": data.get("overall_distortion", 0),
            "most_damaging_effect": data.get("most_damaging_effect", ""),
            "what_we_dont_see": data.get("what_we_dont_see", ""),
            "corrected_conclusion": data.get("corrected_conclusion", ""),
            "data_needed_to_correct": data.get("data_needed_to_correct", ""),
        }
