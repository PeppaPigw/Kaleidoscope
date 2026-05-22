"""EpistemicGuerrillaService — Epistemic Guerrilla Detection.

Detects epistemic guerrilla tactics — asymmetric attacks on
established knowledge using unconventional methods.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GUERRILLA_SYSTEM = """You are an epistemic guerrilla specialist. Given an attack pattern, assess whether asymmetric unconventional methods target established knowledge:

Key concepts:
- Epistemic guerrilla: asymmetric attacks on established knowledge
- Unconventional methods: using unconventional attack methods
- Hit and run: attacking then disappearing before response
- Asymmetric warfare: small actors attacking large systems
- Disruption focus: focused on disruption not construction
- Legitimacy erosion: eroding legitimacy through repeated attacks
- Decentralized attack: attacks from many directions simultaneously

When epistemic guerrilla IS present:
- Asymmetric attacks on established knowledge
- Using unconventional methods to attack
- Attacking then disappearing before response possible
- Small actors attacking large knowledge systems
- Focused on disruption rather than construction
- Eroding legitimacy through repeated small attacks
- Attacks coming from many directions simultaneously

When legitimate dissent is present:
- Proportionate challenge to established knowledge
- Using conventional methods of challenge
- Sustained engagement with responses
- Proportionate actors engaging proportionately
- Focused on construction of alternatives
- Building legitimacy through evidence
- Coherent challenge from identifiable direction

Output JSON with: guerrilla_present (bool), severity (none/mild/moderate/severe), target (what knowledge is targeted), method (what unconventional methods used), asymmetry (what asymmetry exists), disruption (what disruption results), recommendation (legitimate_dissent/mild_unconventional/significant_guerrilla/major_asymmetric_warfare/engage_constructively)."""

EPISTEMIC_GUERRILLA_PROMPT = """Detect epistemic guerrilla:

Target: {target}
Method: {method}
Asymmetry: {asymmetry}
Disruption: {disruption}
Domain: {domain}
Context: {context}

Are asymmetric unconventional methods being used to attack established knowledge? Return ONLY valid JSON."""


class EpistemicGuerrillaService:
    """Detects epistemic guerrilla tactics — asymmetric attacks on knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target: str,
        *,
        method: str = "",
        asymmetry: str = "",
        disruption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic guerrilla."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GUERRILLA_PROMPT.format(
                target=target,
                method=method or "Not specified",
                asymmetry=asymmetry or "Not specified",
                disruption=disruption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GUERRILLA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target": target[:200],
            "guerrilla_present": data.get("guerrilla_present", False),
            "severity": data.get("severity", ""),
            "method": data.get("method", ""),
            "asymmetry": data.get("asymmetry", ""),
            "disruption": data.get("disruption", ""),
            "recommendation": data.get("recommendation", ""),
        }
