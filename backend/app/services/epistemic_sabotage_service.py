"""EpistemicSabotageService — Epistemic Sabotage Detection.

Detects epistemic sabotage — deliberate undermining of knowledge
infrastructure from within.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SABOTAGE_SYSTEM = """You are an epistemic sabotage specialist. Given an undermining pattern, assess whether knowledge infrastructure is being deliberately undermined from within:

Key concepts:
- Epistemic sabotage: deliberate undermining from within
- Insider attack: attack from within the system
- Infrastructure damage: damaging knowledge infrastructure
- Trust destruction: destroying trust from inside
- Process corruption: corrupting knowledge processes
- Standard erosion: eroding standards from within
- Institutional hollowing: hollowing out institutions from inside

When epistemic sabotage IS present:
- Deliberate undermining of knowledge infrastructure from within
- Attack coming from inside the system
- Damaging knowledge infrastructure deliberately
- Destroying trust from an insider position
- Corrupting knowledge processes from within
- Eroding standards from inside the institution
- Hollowing out institutions from the inside

When legitimate reform is present:
- Constructive criticism from within
- Reform aimed at improvement
- Strengthening knowledge infrastructure
- Building trust through transparency
- Improving knowledge processes
- Raising standards from within
- Strengthening institutions through reform

Output JSON with: sabotage_present (bool), severity (none/mild/moderate/severe), target (what is being sabotaged), insider (who is the insider), method (how sabotage occurs), damage (what damage results), recommendation (legitimate_reform/mild_undermining/significant_sabotage/major_institutional_hollowing/protect_infrastructure)."""

EPISTEMIC_SABOTAGE_PROMPT = """Detect epistemic sabotage:

Target: {target}
Insider: {insider}
Method: {method}
Damage: {damage}
Domain: {domain}
Context: {context}

Is knowledge infrastructure being deliberately undermined from within? Return ONLY valid JSON."""


class EpistemicSabotageService:
    """Detects epistemic sabotage — deliberate undermining from within."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target: str,
        *,
        insider: str = "",
        method: str = "",
        damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sabotage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SABOTAGE_PROMPT.format(
                target=target,
                insider=insider or "Not specified",
                method=method or "Not specified",
                damage=damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SABOTAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target": target[:200],
            "sabotage_present": data.get("sabotage_present", False),
            "severity": data.get("severity", ""),
            "insider": data.get("insider", ""),
            "method": data.get("method", ""),
            "damage": data.get("damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
