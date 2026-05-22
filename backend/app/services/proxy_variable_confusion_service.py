"""ProxyVariableConfusionService — Proxy Variable Confusion Detection.

Detects proxy variable confusion — confusing the proxy with the
thing it measures, treating the indicator as if it were the
underlying construct itself.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROXY_VARIABLE_CONFUSION_SYSTEM = """You are a proxy variable confusion specialist. Given a measurement claim, assess whether a proxy is being confused with the thing it measures:

Key concepts:
- Proxy variable: measurable stand-in for unmeasurable construct
- Construct validity: whether proxy actually measures the construct
- Reification: treating abstract construct as concrete thing
- Indicator vs construct: the map vs the territory
- Proxy drift: proxy diverging from construct over time
- Multiple indicators: using several proxies to triangulate
- Validity threats: reasons proxy might not represent construct

When proxy confusion IS present:
- Proxy treated as identical to the construct
- Decisions made on proxy without considering validity
- Proxy limitations not acknowledged
- Single proxy used for complex construct
- Proxy drift not monitored
- Construct validity not established
- Proxy reified as the real thing

When proxy use is appropriate:
- Proxy explicitly acknowledged as proxy
- Construct validity established
- Limitations of proxy discussed
- Multiple proxies used for triangulation
- Proxy drift monitored over time
- Decisions qualified by proxy limitations
- Distinction between proxy and construct maintained

Output JSON with: confusion_present (bool), severity (none/mild/moderate/severe), proxy (what proxy is used), construct (what it's meant to measure), validity_gap (how proxy differs from construct), reification (how proxy is treated as real thing), recommendation (proxy_acknowledged/mild_conflation/significant_confusion/major_reification/distinguish_proxy_from_construct)."""

PROXY_VARIABLE_CONFUSION_PROMPT = """Detect proxy variable confusion:

Claim: {claim}
Proxy used: {proxy}
Construct intended: {construct}
Validity evidence: {validity}
Domain: {domain}
Context: {context}

Is the proxy being confused with the thing it measures? Return ONLY valid JSON."""


class ProxyVariableConfusionService:
    """Detects proxy variable confusion — confusing indicator with construct."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        proxy: str = "",
        construct: str = "",
        validity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect proxy variable confusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROXY_VARIABLE_CONFUSION_PROMPT.format(
                claim=claim,
                proxy=proxy or "Not specified",
                construct=construct or "Not specified",
                validity=validity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROXY_VARIABLE_CONFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "confusion_present": data.get("confusion_present", False),
            "severity": data.get("severity", ""),
            "proxy": data.get("proxy", ""),
            "construct": data.get("construct", ""),
            "validity_gap": data.get("validity_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
