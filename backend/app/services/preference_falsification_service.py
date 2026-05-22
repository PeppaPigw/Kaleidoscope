"""PreferenceFalsificationService — Preference Falsification Detection.

Identifies when people publicly state preferences that differ from
their private beliefs (Timur Kuran). Explains why revolutions seem
sudden, why polls fail, and why apparent consensus can collapse
overnight. The gap between public and private preferences creates
fragile social equilibria.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PREF_FALSIFICATION_SYSTEM = """You are a preference falsification specialist. Given a situation, assess whether preference falsification is occurring:
- Are people publicly stating preferences that differ from their private beliefs?
- Is there social pressure making honest expression costly?
- Could the apparent consensus collapse if a few people spoke honestly?
- Is there a preference cascade waiting to happen?
- What would it take to trigger a cascade of honest revelation?

Output JSON with: falsification_likely (bool), severity (none/mild/moderate/severe/extreme), public_preference (what people publicly claim to believe/want), private_preference (what they likely actually believe/want), gap_size (how different public and private preferences are: small/moderate/large/enormous), social_pressure_source (what makes honest expression costly), cost_of_honesty (what happens to those who express true preferences), preference_cascade_risk (0-1 — likelihood of sudden preference revelation), cascade_trigger (what could cause the cascade), tipping_point (how many honest voices needed to trigger cascade), pluralistic_ignorance (bool — does everyone privately disagree but think they're alone?), spiral_of_silence (bool — are dissenters self-censoring?), emperor_has_no_clothes (bool — is the falsification obvious but unspoken?), who_benefits_from_falsification (who gains from maintaining the false consensus), historical_parallels (similar situations where preferences suddenly revealed), fragility_of_consensus (0-1 — how fragile is the current apparent agreement), recommendation (consensus_genuine/monitor_for_cascade/create_safe_expression/expect_reversal)."""

PREF_FALSIFICATION_PROMPT = """Detect preference falsification:

Situation: {situation}
Apparent consensus: {consensus}
Social pressure: {pressure}
Private signals: {private_signals}
Domain: {domain}
Context: {context}

Is preference falsification occurring? Return ONLY valid JSON."""


class PreferenceFalsificationService:
    """Detects preference falsification — gap between public and private beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        consensus: str = "",
        pressure: str = "",
        private_signals: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect preference falsification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PREF_FALSIFICATION_PROMPT.format(
                situation=situation,
                consensus=consensus or "Not specified",
                pressure=pressure or "Not specified",
                private_signals=private_signals or "None noted",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PREF_FALSIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "falsification_likely": data.get("falsification_likely", False),
            "severity": data.get("severity", ""),
            "public_preference": data.get("public_preference", ""),
            "private_preference": data.get("private_preference", ""),
            "gap_size": data.get("gap_size", ""),
            "social_pressure_source": data.get("social_pressure_source", ""),
            "cost_of_honesty": data.get("cost_of_honesty", ""),
            "preference_cascade_risk": data.get("preference_cascade_risk", 0),
            "cascade_trigger": data.get("cascade_trigger", ""),
            "tipping_point": data.get("tipping_point", ""),
            "pluralistic_ignorance": data.get("pluralistic_ignorance", False),
            "spiral_of_silence": data.get("spiral_of_silence", False),
            "emperor_has_no_clothes": data.get("emperor_has_no_clothes", False),
            "who_benefits_from_falsification": data.get("who_benefits_from_falsification", ""),
            "historical_parallels": data.get("historical_parallels", []),
            "fragility_of_consensus": data.get("fragility_of_consensus", 0),
            "recommendation": data.get("recommendation", ""),
        }
