"""PluristicIgnoranceService — Pluralistic Ignorance Detection.

Detects pluralistic ignorance — where the majority privately
rejects a norm/belief but each individual assumes everyone else
accepts it, so no one speaks up. The emperor has no clothes.
Everyone is pretending. Related to preference falsification but
focused on the collective delusion aspect.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PLURALISTIC_SYSTEM = """You are a pluralistic ignorance specialist. Given a social situation, assess whether pluralistic ignorance is maintaining a norm that most people privately reject:

Key concepts:
- Everyone privately disagrees but publicly conforms
- Each person thinks they're the only one who disagrees
- The norm persists because no one knows others also reject it
- First-mover problem: speaking up is risky if you think you're alone
- Cascade potential: once someone speaks up, rapid norm collapse is possible
- Related to: preference falsification, spiral of silence, bystander effect

Classic examples:
- Students who all think they're the only one confused in class
- Employees who all hate a policy but think everyone else supports it
- Social norms maintained by mutual misperception of others' beliefs

Output JSON with: pluralistic_ignorance_likely (bool), severity (none/mild/moderate/severe/extreme), public_norm (what people publicly appear to believe/support), private_belief (what people likely actually think), gap_size (how large the public-private gap is: small/moderate/large/enormous), conformity_mechanism (what keeps people publicly conforming: fear/politeness/career_risk/social_pressure), first_mover_cost (what happens to the first person who speaks up), cascade_potential (0-1 — how likely rapid norm collapse is if someone breaks silence), evidence_of_private_dissent (what signals suggest private disagreement), who_benefits_from_ignorance (who gains from the false consensus), who_would_benefit_from_truth (who gains if the real distribution of beliefs is revealed), historical_analogues (similar situations where pluralistic ignorance collapsed), tipping_point (what would trigger the cascade), anonymous_vs_public (would anonymous polling reveal different beliefs?), recommendation (no_ignorance/mild_misperception/significant_ignorance/norm_ripe_for_collapse/facilitate_revelation)."""

PLURALISTIC_PROMPT = """Detect pluralistic ignorance:

Situation: {situation}
Public behavior: {public_behavior}
Private signals: {private_signals}
Conformity pressure: {pressure}
Domain: {domain}
Context: {context}

Is pluralistic ignorance maintaining a false consensus? Return ONLY valid JSON."""


class PluristicIgnoranceService:
    """Detects pluralistic ignorance — false consensus from mutual misperception."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        public_behavior: str = "",
        private_signals: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect pluralistic ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PLURALISTIC_PROMPT.format(
                situation=situation,
                public_behavior=public_behavior or "Not specified",
                private_signals=private_signals or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PLURALISTIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "pluralistic_ignorance_likely": data.get("pluralistic_ignorance_likely", False),
            "severity": data.get("severity", ""),
            "public_norm": data.get("public_norm", ""),
            "private_belief": data.get("private_belief", ""),
            "gap_size": data.get("gap_size", ""),
            "conformity_mechanism": data.get("conformity_mechanism", ""),
            "first_mover_cost": data.get("first_mover_cost", ""),
            "cascade_potential": data.get("cascade_potential", 0),
            "evidence_of_private_dissent": data.get("evidence_of_private_dissent", ""),
            "who_benefits_from_ignorance": data.get("who_benefits_from_ignorance", ""),
            "who_would_benefit_from_truth": data.get("who_would_benefit_from_truth", ""),
            "historical_analogues": data.get("historical_analogues", []),
            "tipping_point": data.get("tipping_point", ""),
            "anonymous_vs_public": data.get("anonymous_vs_public", ""),
            "recommendation": data.get("recommendation", ""),
        }
