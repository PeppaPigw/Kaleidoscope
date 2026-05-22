"""EpistemicTidePoolService — Epistemic Tide Pool Detection.

Detects epistemic tide pools — small isolated intellectual ecosystems
that form when the main body of knowledge recedes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TIDE_POOL_SYSTEM = """You are an epistemic tide pool specialist. Given an isolated knowledge pocket, assess whether small ecosystems form when main knowledge recedes:

Key concepts:
- Epistemic tide pool: small isolated ecosystem from receding knowledge
- Isolation: cut off from main body of knowledge
- Microecosystem: unique intellectual life in small space
- Tidal cycle: periodic connection and disconnection from main body
- Adaptation: ideas adapting to isolated conditions
- Vulnerability: exposed to harsh conditions between tides
- Diversity: surprising diversity in small isolated space

When epistemic tide pool IS present:
- Small isolated intellectual ecosystems forming
- Cut off from main body of knowledge
- Unique intellectual life developing in small space
- Periodic connection and disconnection from mainstream
- Ideas adapting to isolated conditions
- Vulnerability to harsh conditions during isolation
- Surprising diversity in small isolated space

When connected knowledge is present:
- Knowledge fully connected to main body
- No isolation from mainstream
- Ideas developing in full context
- Continuous connection to broader knowledge
- No need for special adaptation
- Protected by connection to larger body
- Diversity proportional to space

Output JSON with: tide_pool_present (bool), severity (none/mild/moderate/severe), pool (what isolated ecosystem exists), isolation (what cuts it off), microecosystem (what unique life develops), vulnerability (what harsh conditions threaten), recommendation (connected_knowledge/mild_isolation/significant_tide_pool/major_isolated_ecosystem/reconnect_or_protect_diversity)."""

EPISTEMIC_TIDE_POOL_PROMPT = """Detect epistemic tide pool:

Pool: {pool}
Isolation: {isolation}
Microecosystem: {microecosystem}
Vulnerability: {vulnerability}
Domain: {domain}
Context: {context}

Are small isolated intellectual ecosystems forming where the main body of knowledge has receded? Return ONLY valid JSON."""


class EpistemicTidePoolService:
    """Detects epistemic tide pools — isolated ecosystems from receding knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pool: str,
        *,
        isolation: str = "",
        microecosystem: str = "",
        vulnerability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tide pool."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TIDE_POOL_PROMPT.format(
                pool=pool,
                isolation=isolation or "Not specified",
                microecosystem=microecosystem or "Not specified",
                vulnerability=vulnerability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TIDE_POOL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pool": pool[:200],
            "tide_pool_present": data.get("tide_pool_present", False),
            "severity": data.get("severity", ""),
            "isolation": data.get("isolation", ""),
            "microecosystem": data.get("microecosystem", ""),
            "vulnerability": data.get("vulnerability", ""),
            "recommendation": data.get("recommendation", ""),
        }
