"""PluristicIgnoranceEpistemicService — Pluralistic Ignorance Detection.

Detects epistemic pluralistic ignorance — situations where everyone
privately doubts a belief but publicly agrees, creating a false
consensus that no individual actually endorses.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PLURALISTIC_IGNORANCE_EPISTEMIC_SYSTEM = """You are an epistemic pluralistic ignorance specialist. Given a group belief, assess whether private doubt coexists with public agreement:

Key concepts:
- Pluralistic ignorance: private doubt with public agreement
- False consensus: everyone thinks everyone else believes
- Preference falsification: hiding true beliefs
- Spiral of silence: silence interpreted as agreement
- Emperor's new clothes: no one speaks the obvious
- Social desirability masking: hiding doubt for acceptance
- Collective self-deception: group deceives itself

When pluralistic ignorance IS present:
- Private doubt widespread but unexpressed
- Public agreement masks private disagreement
- Everyone assumes others genuinely believe
- Silence interpreted as endorsement
- Social pressure prevents expressing doubt
- False consensus maintained by mutual silence
- Individual doubt hidden for social acceptance

When genuine consensus is present:
- Public and private beliefs aligned
- Disagreement can be safely expressed
- Consensus tested through anonymous channels
- Agreement robust to private polling
- Social pressure not preventing dissent
- Individuals genuinely endorse the position
- Consensus survives when anonymity provided

Output JSON with: ignorance_present (bool), severity (none/mild/moderate/severe), belief (what belief is publicly held), private_doubt (what doubt exists privately), mechanism (how silence is maintained), false_consensus (what false consensus results), recommendation (genuine_consensus/mild_preference_hiding/significant_pluralistic_ignorance/major_collective_self_deception/create_safe_channels_for_doubt)."""

PLURALISTIC_IGNORANCE_EPISTEMIC_PROMPT = """Detect epistemic pluralistic ignorance:

Belief: {belief}
Public expression: {public}
Private indicators: {private}
Social pressure: {pressure}
Domain: {domain}
Context: {context}

Does private doubt coexist with public agreement creating false consensus? Return ONLY valid JSON."""


class PluristicIgnoranceEpistemicService:
    """Detects epistemic pluralistic ignorance — private doubt with public agreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        public: str = "",
        private: str = "",
        pressure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pluralistic ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PLURALISTIC_IGNORANCE_EPISTEMIC_PROMPT.format(
                belief=belief,
                public=public or "Not specified",
                private=private or "Not specified",
                pressure=pressure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PLURALISTIC_IGNORANCE_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "ignorance_present": data.get("ignorance_present", False),
            "severity": data.get("severity", ""),
            "private_doubt": data.get("private_doubt", ""),
            "mechanism": data.get("mechanism", ""),
            "false_consensus": data.get("false_consensus", ""),
            "recommendation": data.get("recommendation", ""),
        }
