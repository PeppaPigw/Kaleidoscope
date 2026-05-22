"""DomainBoundaryViolationService — Domain Boundary Violation Detection.

Detects domain boundary violations — applying domain-specific norms,
methods, or standards outside their valid domain, where rules that
work in one context are imposed on a different context.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DOMAIN_BOUNDARY_VIOLATION_SYSTEM = """You are a domain boundary violation specialist. Given an application of norms, assess whether domain-specific rules are being applied outside their valid domain:

Key concepts:
- Domain boundary violation: norms applied outside valid domain
- Context misapplication: rules from one context imposed on another
- Methodological imperialism: one domain's methods imposed on all
- Standard transplantation: standards moved without adaptation
- Domain-specific validity: norms valid only within their domain
- Cross-domain imposition: forcing one domain's rules on another
- Contextual inappropriateness: appropriate there, inappropriate here

When domain boundary violation IS present:
- Domain-specific norms applied outside their valid context
- Methods from one domain imposed on another without justification
- Standards transplanted without adaptation to new domain
- Rules valid in one context forced on different context
- One domain's methodology treated as universal
- Context-specific appropriateness ignored
- Domain boundaries not respected

When cross-domain application is appropriate:
- Transfer explicitly justified
- Adaptation to new domain made
- Limitations of transfer acknowledged
- Domain-specific validity respected
- Cross-domain application tested
- Context differences accounted for
- Transfer improves rather than distorts

Output JSON with: violation_present (bool), severity (none/mild/moderate/severe), application (what is being applied), source_domain (where norms come from), target_domain (where norms are applied), mismatch (what doesn't fit), recommendation (appropriate_cross_domain/mild_context_stretch/significant_domain_violation/major_methodological_imperialism/respect_domain_boundaries)."""

DOMAIN_BOUNDARY_VIOLATION_PROMPT = """Detect domain boundary violation:

Application: {application}
Source domain: {source}
Target domain: {target}
Justification: {justification}
Domain: {domain}
Context: {context}

Are domain-specific norms being applied outside their valid domain? Return ONLY valid JSON."""


class DomainBoundaryViolationService:
    """Detects domain boundary violations — norms applied outside valid domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        application: str,
        *,
        source: str = "",
        target: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect domain boundary violation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DOMAIN_BOUNDARY_VIOLATION_PROMPT.format(
                application=application,
                source=source or "Not specified",
                target=target or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DOMAIN_BOUNDARY_VIOLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "application": application[:200],
            "violation_present": data.get("violation_present", False),
            "severity": data.get("severity", ""),
            "source_domain": data.get("source_domain", ""),
            "target_domain": data.get("target_domain", ""),
            "mismatch": data.get("mismatch", ""),
            "recommendation": data.get("recommendation", ""),
        }
