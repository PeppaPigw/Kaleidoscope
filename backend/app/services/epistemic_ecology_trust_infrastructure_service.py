"""EpistemicEcologyTrustInfrastructureService - Trust Infrastructure Decay Detection.

Detects trust infrastructure decay where institutions enabling trust are degraded.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ECOLOGY_TRUST_INFRASTRUCTURE_SYSTEM = """You are an epistemic ecology trust infrastructure specialist. Given institutional trust decay, assess whether institutions enabling trust are degraded:

Key concepts:
- Trust infrastructure decay: institutions and systems that support warranted trust losing reliability
- Institutional trust decay: confidence in trust-enabling institutions eroding
- Verification system failure: mechanisms for checking claims failing
- Reputation system gaming: reputation signals being manipulated
- Credential inflation: credentials losing signal value through overproduction or dilution

When trust infrastructure decay IS present:
- Institutional trust decays
- Verification systems fail or become inaccessible
- Reputation systems are gamed
- Credentials inflate and lose signal value
- Warranted trust becomes harder to establish

When no trust infrastructure decay:
- Institutions preserve warranted trust
- Verification systems remain functional
- Reputation signals resist gaming
- Credentials retain calibrated signal value
- Trust can be established through reliable infrastructure

Output JSON with: decay_detected (bool), severity (none/mild/moderate/severe), verification_system_failure (how verification fails), reputation_system_gaming (how reputation is gamed), credential_inflation (how credentials lose signal value), recommendation (no_decay/mild_trust_maintenance/significant_verification_repair/major_infrastructure_rebuild/emergency_trust_restoration)."""

EPISTEMIC_ECOLOGY_TRUST_INFRASTRUCTURE_PROMPT = """Detect epistemic ecology trust infrastructure decay:

Institutional trust decay: {institutional_trust_decay}
Verification system failure: {verification_system_failure}
Reputation system gaming: {reputation_system_gaming}
Credential inflation: {credential_inflation}
Domain: {domain}
Context: {context}

Are institutions enabling trust being degraded? Return ONLY valid JSON."""


class EpistemicEcologyTrustInfrastructureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        institutional_trust_decay: str,
        *,
        verification_system_failure: str = "",
        reputation_system_gaming: str = "",
        credential_inflation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ECOLOGY_TRUST_INFRASTRUCTURE_PROMPT.format(
                institutional_trust_decay=institutional_trust_decay,
                verification_system_failure=verification_system_failure or "Not specified",
                reputation_system_gaming=reputation_system_gaming or "Not specified",
                credential_inflation=credential_inflation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ECOLOGY_TRUST_INFRASTRUCTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "institutional_trust_decay": institutional_trust_decay[:200],
            "decay_detected": data.get("decay_detected", False),
            "severity": data.get("severity", ""),
            "verification_system_failure": data.get("verification_system_failure", ""),
            "reputation_system_gaming": data.get("reputation_system_gaming", ""),
            "credential_inflation": data.get("credential_inflation", ""),
            "recommendation": data.get("recommendation", ""),
        }
