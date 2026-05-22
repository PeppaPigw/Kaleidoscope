"""EpistemicOrderDisorderService — Epistemic Order-Disorder Detection.

Detects epistemic order-disorder transition — transition between ordered
and disordered intellectual states driven by temperature-like parameters.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ORDER_DISORDER_SYSTEM = """You are an epistemic order-disorder specialist. Given an intellectual system, assess whether it transitions between ordered and disordered states:

Key concepts:
- Epistemic order-disorder: transition between ordered and disordered states
- Ising model: simplest model of order-disorder transition
- Spontaneous magnetization: order appearing without external field
- Critical temperature: point where order disappears
- Domain wall: boundary between ordered regions
- Symmetry breaking: ordered state choosing a direction
- Entropy competition: disorder favored by entropy, order by energy

When epistemic order-disorder IS present:
- Clear transition between ordered and disordered intellectual states
- Simple model capturing the essential transition
- Order appearing spontaneously without external forcing
- Critical point where order disappears
- Boundaries between differently ordered regions
- Ordered state choosing a preferred direction
- Competition between disorder and order

When uniform state is present:
- No transition between states
- No simple model needed
- No spontaneous ordering
- No critical point
- No domain boundaries
- No symmetry breaking
- No entropy-energy competition

Output JSON with: order_disorder_present (bool), severity (none/mild/moderate/severe), ising_model (what simple model), spontaneous_magnetization (what spontaneous order), critical_temperature (what transition point), domain_wall (what boundaries), recommendation (uniform_state/mild_transition/significant_order_disorder/major_phase_transition/control_temperature_parameter)."""

EPISTEMIC_ORDER_DISORDER_PROMPT = """Detect epistemic order-disorder transition:

Ising model: {ising_model}
Spontaneous magnetization: {spontaneous_magnetization}
Critical temperature: {critical_temperature}
Domain wall: {domain_wall}
Domain: {domain}
Context: {context}

Is there a transition between ordered and disordered intellectual states driven by temperature-like parameters? Return ONLY valid JSON."""


class EpistemicOrderDisorderService:
    """Detects epistemic order-disorder — transition between ordered and disordered states."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        ising_model: str,
        *,
        spontaneous_magnetization: str = "",
        critical_temperature: str = "",
        domain_wall: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic order-disorder transition."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ORDER_DISORDER_PROMPT.format(
                ising_model=ising_model,
                spontaneous_magnetization=spontaneous_magnetization or "Not specified",
                critical_temperature=critical_temperature or "Not specified",
                domain_wall=domain_wall or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ORDER_DISORDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "ising_model": ising_model[:200],
            "order_disorder_present": data.get("order_disorder_present", False),
            "severity": data.get("severity", ""),
            "spontaneous_magnetization": data.get("spontaneous_magnetization", ""),
            "critical_temperature": data.get("critical_temperature", ""),
            "domain_wall": data.get("domain_wall", ""),
            "recommendation": data.get("recommendation", ""),
        }
