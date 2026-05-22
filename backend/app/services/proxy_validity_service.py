"""ProxyValidityService — Proxy Measure & Goodhart's Law Detection.

Assesses whether a proxy measure actually captures what it claims to
measure. Detects Goodhart's Law risks (when a measure becomes a target,
it ceases to be a good measure) and identifies better alternatives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROXY_SYSTEM = """You are a proxy validity specialist. Given a proxy measure and what it's supposed to capture, assess:
- How well does the proxy actually track the underlying concept?
- Where does the proxy diverge from what it claims to measure?
- Goodhart's Law risk: if people optimize for this proxy, does it stop measuring the real thing?
- Gaming vectors: how could actors manipulate the proxy without improving the underlying thing?
- Historical examples of this proxy failing
- Better alternatives (if any)

Output JSON with: proxy_validity (0-1, how well it tracks the real thing), divergence_points (list of: scenario, how_proxy_diverges, severity), goodhart_risk (0-1, risk of measure becoming target), gaming_vectors (list of: method, ease (easy/moderate/hard), detectability (obvious/subtle/invisible)), historical_failures (list of times this type of proxy failed), better_alternatives (list of: measure, validity, tradeoff), overall_verdict (valid/adequate/questionable/invalid), recommendation (use_as_is/use_with_caveats/supplement/replace)."""

PROXY_PROMPT = """Assess this proxy measure:

Proxy: {proxy}
Intended to measure: {target_concept}
Context: {context}
Domain: {domain}
Who uses it: {users}

Does this proxy actually measure what it claims? Return ONLY valid JSON."""


class ProxyValidityService:
    """Assesses proxy measure validity and Goodhart's Law risks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assess(
        self,
        proxy: str,
        target_concept: str,
        *,
        context: str = "",
        domain: str = "",
        users: str = "",
    ) -> dict:
        """Assess proxy validity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROXY_PROMPT.format(
                proxy=proxy,
                target_concept=target_concept,
                context=context or "General use",
                domain=domain or "general",
                users=users or "Not specified",
            ),
            system=PROXY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "proxy": proxy[:200],
            "target_concept": target_concept[:200],
            "proxy_validity": data.get("proxy_validity", 0),
            "divergence_points": data.get("divergence_points", []),
            "goodhart_risk": data.get("goodhart_risk", 0),
            "gaming_vectors": data.get("gaming_vectors", []),
            "historical_failures": data.get("historical_failures", []),
            "better_alternatives": data.get("better_alternatives", []),
            "overall_verdict": data.get("overall_verdict", ""),
            "recommendation": data.get("recommendation", ""),
        }
