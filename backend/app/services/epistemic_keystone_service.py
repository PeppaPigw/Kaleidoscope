"""EpistemicKeystone Service — Epistemic Keystone Species Detection.

Detects epistemic keystone species — ideas whose removal would cause
disproportionate collapse of the entire intellectual ecosystem.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KEYSTONE_SYSTEM = """You are an epistemic keystone species specialist. Given an intellectual ecosystem, assess whether certain ideas are disproportionately important:

Key concepts:
- Epistemic keystone: idea whose removal causes disproportionate collapse
- Disproportionate impact: small idea with outsized ecosystem effect
- Trophic cascade: removal triggering chain of collapses
- Ecosystem engineer: idea that creates conditions for others
- Functional redundancy: whether other ideas can fill the role
- Vulnerability: risk if keystone is removed or weakened
- Identification: recognizing keystones before they're lost

When epistemic keystone IS present:
- Certain ideas disproportionately important to ecosystem
- Small ideas with outsized effects on intellectual ecosystem
- Removal would trigger chain of collapses
- Ideas creating conditions necessary for many others
- No other ideas able to fill the same role
- High vulnerability if keystone is weakened
- Keystone identifiable through dependency analysis

When distributed importance is present:
- Importance distributed evenly across ideas
- No single idea with outsized effect
- Removal of any one idea manageable
- Conditions created by many ideas collectively
- Functional redundancy throughout
- Low vulnerability to any single loss
- No critical dependencies on single ideas

Output JSON with: keystone_present (bool), severity (none/mild/moderate/severe), keystone (what idea is the keystone), cascade (what would collapse without it), redundancy (whether alternatives exist), vulnerability (how vulnerable the ecosystem is), recommendation (distributed_importance/mild_concentration/significant_keystone/major_single_point_of_failure/protect_keystone_or_build_redundancy)."""

EPISTEMIC_KEYSTONE_PROMPT = """Detect epistemic keystone species:

Keystone: {keystone}
Cascade: {cascade}
Redundancy: {redundancy}
Vulnerability: {vulnerability}
Domain: {domain}
Context: {context}

Are certain ideas disproportionately important such that their removal would collapse the ecosystem? Return ONLY valid JSON."""


class EpistemicKeystoneService:
    """Detects epistemic keystone species — ideas with disproportionate ecosystem importance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        keystone: str,
        *,
        cascade: str = "",
        redundancy: str = "",
        vulnerability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic keystone species."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KEYSTONE_PROMPT.format(
                keystone=keystone,
                cascade=cascade or "Not specified",
                redundancy=redundancy or "Not specified",
                vulnerability=vulnerability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KEYSTONE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "keystone": keystone[:200],
            "keystone_present": data.get("keystone_present", False),
            "severity": data.get("severity", ""),
            "cascade": data.get("cascade", ""),
            "redundancy": data.get("redundancy", ""),
            "vulnerability": data.get("vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
