"""EpistemicMeltService — Epistemic Melt Detection.

Detects epistemic melt — previously solid intellectual structures
liquefying under warming conditions, losing their form and function.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MELT_SYSTEM = """You are an epistemic melt specialist. Given an intellectual structure, assess whether warming conditions are causing it to liquify:

Key concepts:
- Epistemic melt: solid intellectual structures liquefying
- Warming conditions: intellectual environment becoming too warm
- Loss of form: structures losing their defined shape
- Loss of function: structures no longer serving their purpose
- Meltwater: liquid ideas flowing from melting structures
- Sea level rise: rising tide of undifferentiated ideas
- Point of no return: when melting becomes irreversible

When epistemic melt IS present:
- Previously solid intellectual structures liquefying
- Intellectual environment warming beyond structure tolerance
- Structures losing their defined shape and boundaries
- Structures no longer serving their original purpose
- Liquid undifferentiated ideas flowing from melting structures
- Rising tide of undifferentiated ideas from melting
- Melting approaching or past point of no return

When solid structures are present:
- Intellectual structures maintaining solid form
- Environment within tolerance of structures
- Structures maintaining defined shape and boundaries
- Structures serving their purpose effectively
- Ideas remaining in structured form
- No rising tide of undifferentiated ideas
- Structures stable and sustainable

Output JSON with: melt_present (bool), severity (none/mild/moderate/severe), structure (what structure melts), warming (what warming causes it), loss_of_form (what shape is lost), meltwater (what undifferentiated ideas result), recommendation (solid_structures/mild_softening/significant_melt/major_liquefaction/cool_environment_or_rebuild)."""

EPISTEMIC_MELT_PROMPT = """Detect epistemic melt:

Structure: {structure}
Warming: {warming}
Loss of form: {loss_of_form}
Meltwater: {meltwater}
Domain: {domain}
Context: {context}

Are previously solid intellectual structures liquefying under warming conditions? Return ONLY valid JSON."""


class EpistemicMeltService:
    """Detects epistemic melt — solid structures liquefying under warming."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        warming: str = "",
        loss_of_form: str = "",
        meltwater: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic melt."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MELT_PROMPT.format(
                structure=structure,
                warming=warming or "Not specified",
                loss_of_form=loss_of_form or "Not specified",
                meltwater=meltwater or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MELT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "melt_present": data.get("melt_present", False),
            "severity": data.get("severity", ""),
            "warming": data.get("warming", ""),
            "loss_of_form": data.get("loss_of_form", ""),
            "meltwater": data.get("meltwater", ""),
            "recommendation": data.get("recommendation", ""),
        }
