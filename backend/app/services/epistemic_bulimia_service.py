"""EpistemicBulimiaService — Epistemic Bulimia Detection.

Detects epistemic bulimia — binge-purge cycle of consuming massive
amounts of information then purging through rejection or forgetting.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BULIMIA_SYSTEM = """You are an epistemic bulimia specialist. Given binge-purge intellectual patterns, assess bulimia:

Key concepts:
- Epistemic bulimia: binge-purge cycle with information
- Binge: consuming massive amounts of information rapidly
- Purge: rejecting, forgetting, or discarding what was consumed
- Compensatory behavior: excessive criticism after intake
- Shame cycle: guilt about intellectual consumption
- Loss of control: inability to moderate intake
- Secrecy: hiding intellectual consumption patterns

When epistemic bulimia IS present:
- Binge-purge cycle with information
- Consuming massive amounts rapidly
- Rejecting what was consumed
- Excessive criticism after intake
- Guilt about consumption
- Inability to moderate
- Hiding consumption patterns

When no bulimia:
- Steady intellectual intake
- Retaining what is consumed
- No rejection cycle
- Proportionate self-assessment
- No guilt about learning
- Moderated intake
- Open about learning

Output JSON with: bulimia_detected (bool), severity (none/mild/moderate/severe), binge_pattern (what overconsumption), purge_mechanism (what rejection), shame_level (what guilt), control_loss (what inability to moderate), recommendation (no_bulimia/mild_structured_intake/significant_cbt/major_intensive_program/emergency_severe_cycle)."""

EPISTEMIC_BULIMIA_PROMPT = """Detect epistemic bulimia:

Binge pattern: {binge_pattern}
Purge mechanism: {purge_mechanism}
Shame level: {shame_level}
Control loss: {control_loss}
Domain: {domain}
Context: {context}

Is there a binge-purge cycle of consuming then rejecting information? Return ONLY valid JSON."""


class EpistemicBulimiaService:
    """Detects epistemic bulimia — binge-purge cycle with information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        binge_pattern: str,
        *,
        purge_mechanism: str = "",
        shame_level: str = "",
        control_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic bulimia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BULIMIA_PROMPT.format(
                binge_pattern=binge_pattern,
                purge_mechanism=purge_mechanism or "Not specified",
                shame_level=shame_level or "Not specified",
                control_loss=control_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BULIMIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "binge_pattern": binge_pattern[:200],
            "bulimia_detected": data.get("bulimia_detected", False),
            "severity": data.get("severity", ""),
            "purge_mechanism": data.get("purge_mechanism", ""),
            "shame_level": data.get("shame_level", ""),
            "control_loss": data.get("control_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
