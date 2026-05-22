"""EpistemicFeigenbaumService — Epistemic Feigenbaum Constant Detection.

Detects epistemic Feigenbaum constant — universal scaling ratios in
intellectual period-doubling cascades approaching chaos.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEIGENBAUM_SYSTEM = """You are an epistemic Feigenbaum constant specialist. Given an intellectual cascade, assess whether universal scaling ratios appear in period-doubling:

Key concepts:
- Epistemic Feigenbaum: universal scaling in period-doubling
- Period doubling: each iteration doubles complexity
- Universal ratio: 4.669... ratio between successive doublings
- Cascade: sequence of doublings approaching chaos
- Accumulation point: parameter value where chaos begins
- Universality: same ratio regardless of specific system
- Renormalization: self-similar structure at each scale

When epistemic Feigenbaum IS present:
- Universal scaling ratios in intellectual cascades
- Each iteration doubling the complexity
- Consistent ratio between successive complexity increases
- Sequence of doublings approaching chaotic reasoning
- Parameter value where ordered thinking breaks down
- Same pattern regardless of specific intellectual domain
- Self-similar structure at each level of complexity

When non-universal scaling is present:
- No consistent scaling ratios
- Complexity not doubling systematically
- Irregular ratios between changes
- No cascade toward chaos
- No accumulation point
- Domain-specific patterns only
- No self-similar structure

Output JSON with: feigenbaum_present (bool), severity (none/mild/moderate/severe), period_doubling (what complexity doubling), universal_ratio (what consistent scaling), cascade (what sequence), accumulation (what chaos onset), recommendation (non_universal/mild_feigenbaum/significant_feigenbaum/major_universal_cascade/interrupt_period_doubling)."""

EPISTEMIC_FEIGENBAUM_PROMPT = """Detect epistemic Feigenbaum constant:

Period doubling: {period_doubling}
Universal ratio: {universal_ratio}
Cascade: {cascade}
Accumulation: {accumulation}
Domain: {domain}
Context: {context}

Are universal scaling ratios appearing in intellectual period-doubling cascades approaching chaos? Return ONLY valid JSON."""


class EpistemicFeigenbaumService:
    """Detects epistemic Feigenbaum — universal scaling in period-doubling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        period_doubling: str,
        *,
        universal_ratio: str = "",
        cascade: str = "",
        accumulation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Feigenbaum constant."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEIGENBAUM_PROMPT.format(
                period_doubling=period_doubling,
                universal_ratio=universal_ratio or "Not specified",
                cascade=cascade or "Not specified",
                accumulation=accumulation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEIGENBAUM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "period_doubling": period_doubling[:200],
            "feigenbaum_present": data.get("feigenbaum_present", False),
            "severity": data.get("severity", ""),
            "universal_ratio": data.get("universal_ratio", ""),
            "cascade": data.get("cascade", ""),
            "accumulation": data.get("accumulation", ""),
            "recommendation": data.get("recommendation", ""),
        }
