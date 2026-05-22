"""EpistemicGasExchangeService — Epistemic Gas Exchange Detection.

Detects epistemic gas exchange — exchange of fresh ideas for stale ones
at the intellectual membrane where new input replaces exhausted output.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GAS_EXCHANGE_SYSTEM = """You are an epistemic gas exchange specialist. Given an intellectual exchange membrane, assess whether fresh ideas are replacing stale ones:

Key concepts:
- Epistemic gas exchange: fresh ideas replacing stale ones at membrane
- Alveolar surface: interface where exchange occurs
- Diffusion capacity: ability to exchange across membrane
- Partial pressure: driving force for exchange
- Dead space: areas where no exchange occurs
- Shunt: ideas bypassing exchange entirely
- Membrane thickness: barrier to efficient exchange

When epistemic gas exchange IS present:
- Fresh ideas replacing stale ones at interface
- Exchange occurring at intellectual membranes
- Measurable ability to exchange across barriers
- Driving forces pushing exchange
- Areas where no exchange occurs (dead space)
- Ideas bypassing exchange entirely
- Barriers affecting exchange efficiency

When no exchange is present:
- No replacement of stale ideas
- No exchange interface
- No diffusion capacity
- No driving forces
- No dead space concerns
- No shunting
- No membrane barriers

Output JSON with: gas_exchange_present (bool), severity (none/mild/moderate/severe), alveolar_surface (what exchange interface), diffusion_capacity (what exchange ability), dead_space (what non-exchange areas), shunt (what exchange bypass), recommendation (no_exchange/mild_exchange/significant_gas_exchange/major_idea_exchange/optimize_exchange_efficiency)."""

EPISTEMIC_GAS_EXCHANGE_PROMPT = """Detect epistemic gas exchange:

Alveolar surface: {alveolar_surface}
Diffusion capacity: {diffusion_capacity}
Dead space: {dead_space}
Shunt: {shunt}
Domain: {domain}
Context: {context}

Is exchange of fresh ideas for stale ones occurring at the intellectual membrane? Return ONLY valid JSON."""


class EpistemicGasExchangeService:
    """Detects epistemic gas exchange — fresh ideas replacing stale ones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        alveolar_surface: str,
        *,
        diffusion_capacity: str = "",
        dead_space: str = "",
        shunt: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gas exchange."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GAS_EXCHANGE_PROMPT.format(
                alveolar_surface=alveolar_surface,
                diffusion_capacity=diffusion_capacity or "Not specified",
                dead_space=dead_space or "Not specified",
                shunt=shunt or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GAS_EXCHANGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "alveolar_surface": alveolar_surface[:200],
            "gas_exchange_present": data.get("gas_exchange_present", False),
            "severity": data.get("severity", ""),
            "diffusion_capacity": data.get("diffusion_capacity", ""),
            "dead_space": data.get("dead_space", ""),
            "shunt": data.get("shunt", ""),
            "recommendation": data.get("recommendation", ""),
        }
