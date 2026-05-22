"""DescriptiveNormativeSlideService — Descriptive-Normative Slide Detection.

Detects descriptive-normative slide — sliding from "is" to "ought"
without justification, where factual descriptions are treated as
implying normative conclusions without explicit bridging principles.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DESCRIPTIVE_NORMATIVE_SLIDE_SYSTEM = """You are a descriptive-normative slide specialist. Given an argument, assess whether it slides from is to ought without justification:

Key concepts:
- Descriptive-normative slide: moving from is to ought unjustified
- Is-ought gap: Hume's guillotine violated
- Natural as good: treating natural as normatively good
- Statistical as normative: treating common as correct
- Evolutionary as justified: treating evolved as justified
- Traditional as right: treating traditional as normatively right
- Normal as normative: treating statistical normal as norm

When descriptive-normative slide IS present:
- Factual claims treated as implying normative conclusions
- Is-ought gap crossed without bridging principle
- Natural treated as good without justification
- Common treated as correct without argument
- Evolved treated as justified without reasoning
- Traditional treated as right without defense
- Statistical normal treated as normative standard

When is-ought connection is appropriate:
- Bridging principle explicitly stated
- Normative conclusion separately argued
- Factual premises distinguished from normative conclusions
- Is-ought gap acknowledged and addressed
- Natural/common/traditional not assumed good
- Normative claims independently justified
- Descriptive and normative clearly separated

Output JSON with: slide_present (bool), severity (none/mild/moderate/severe), argument (what argument is made), descriptive (what factual claim is made), normative (what normative conclusion is drawn), bridge_missing (what bridging principle is absent), recommendation (appropriate_is_ought_connection/mild_boundary_blur/significant_descriptive_normative_slide/major_unjustified_ought/provide_bridging_principle)."""

DESCRIPTIVE_NORMATIVE_SLIDE_PROMPT = """Detect descriptive-normative slide:

Argument: {argument}
Descriptive claim: {descriptive}
Normative conclusion: {normative}
Bridging principle: {bridge}
Domain: {domain}
Context: {context}

Does this argument slide from is to ought without justification? Return ONLY valid JSON."""


class DescriptiveNormativeSlideService:
    """Detects descriptive-normative slide — unjustified is-to-ought transitions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        descriptive: str = "",
        normative: str = "",
        bridge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect descriptive-normative slide."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DESCRIPTIVE_NORMATIVE_SLIDE_PROMPT.format(
                argument=argument,
                descriptive=descriptive or "Not specified",
                normative=normative or "Not specified",
                bridge=bridge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DESCRIPTIVE_NORMATIVE_SLIDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "slide_present": data.get("slide_present", False),
            "severity": data.get("severity", ""),
            "descriptive": data.get("descriptive", ""),
            "normative": data.get("normative", ""),
            "bridge_missing": data.get("bridge_missing", ""),
            "recommendation": data.get("recommendation", ""),
        }
