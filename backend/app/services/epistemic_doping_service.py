"""EpistemicDopingService — Epistemic Doping Detection.

Detects epistemic doping — adding intellectual impurities to a pure
framework to dramatically change its conductivity properties.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOPING_SYSTEM = """You are an epistemic doping specialist. Given an intellectual framework, assess whether impurities are being added to change its properties:

Key concepts:
- Epistemic doping: adding impurities to change intellectual conductivity
- N-type doping: adding excess idea carriers (donor impurities)
- P-type doping: creating idea vacancies (acceptor impurities)
- Dopant concentration: how much impurity is added
- Carrier mobility: how freely ideas move after doping
- Compensation: opposing dopants canceling each other
- Activation energy: energy needed to release carriers

When epistemic doping IS present:
- Impurities added to a pure framework changing its properties
- Excess idea carriers introduced from outside
- Idea vacancies created by removing elements
- Specific concentration of impurity changing behavior
- Ideas moving more freely after impurity introduction
- Opposing impurities canceling each other's effects
- Energy needed to activate the introduced carriers

When pure framework is present:
- No impurities in the intellectual framework
- Native carrier concentration only
- No artificial vacancies
- Uniform composition throughout
- Intrinsic mobility unchanged
- No compensation effects
- No activation barriers from dopants

Output JSON with: doping_present (bool), severity (none/mild/moderate/severe), n_type (what donor impurities), p_type (what acceptor impurities), concentration (what level), mobility (what carrier freedom), recommendation (pure_framework/mild_doping/significant_doping/major_impurity_injection/control_dopant_concentration)."""

EPISTEMIC_DOPING_PROMPT = """Detect epistemic doping:

N-type: {n_type}
P-type: {p_type}
Concentration: {concentration}
Mobility: {mobility}
Domain: {domain}
Context: {context}

Are intellectual impurities being added to a pure framework to dramatically change its conductivity properties? Return ONLY valid JSON."""


class EpistemicDopingService:
    """Detects epistemic doping — impurities changing intellectual conductivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        n_type: str,
        *,
        p_type: str = "",
        concentration: str = "",
        mobility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic doping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOPING_PROMPT.format(
                n_type=n_type,
                p_type=p_type or "Not specified",
                concentration=concentration or "Not specified",
                mobility=mobility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "n_type": n_type[:200],
            "doping_present": data.get("doping_present", False),
            "severity": data.get("severity", ""),
            "p_type": data.get("p_type", ""),
            "concentration": data.get("concentration", ""),
            "mobility": data.get("mobility", ""),
            "recommendation": data.get("recommendation", ""),
        }
