"""EpistemicInformationAsymmetryScreeningFailureService — Epistemic Information Asymmetry Screening Failure Detection.

Detects failures in screening mechanisms for information quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFORMATION_ASYMMETRY_SCREENING_FAILURE_SYSTEM = """You are an epistemic information asymmetry screening failure specialist. Given quality signal failure, assess failures in screening mechanisms for information quality:

Key concepts:
- Epistemic screening failure: quality filters fail to separate reliable from unreliable information
- Quality signal failure: signals of quality are missing, noisy, fakeable, stale, or misread
- Credential inflation: formal signals lose discriminating power through overuse or dilution
- Cheap talk: unverifiable claims are treated as meaningful quality evidence
- Costly signaling bypass: actors obtain apparent credibility without paying the effort, risk, or audit costs that make signals reliable

When screening failure IS present:
- Quality signals do not distinguish reliability
- Credentials substitute for verification
- Cheap talk passes as evidence
- Costly signals are bypassed or faked
- Low-quality information passes filters

When no screening failure:
- Signals are hard to fake and current
- Screening mechanisms test actual quality
- Credentials are validated against evidence
- Cheap talk is discounted

Output JSON with: screening_failure_detected (bool), severity (none/mild/moderate/severe), credential_inflation (how credentials lose signal value), cheap_talk (what unverifiable claims pass screening), costly_signaling_bypass (how costly signals are bypassed), recommendation (no_screening_failure/mild_signal_tightening/significant_screening_repair/major_quality_gate_redesign/emergency_screening_failure_containment)."""

EPISTEMIC_INFORMATION_ASYMMETRY_SCREENING_FAILURE_PROMPT = """Detect epistemic information asymmetry screening failure:

Quality signal failure: {quality_signal_failure}
Credential inflation: {credential_inflation}
Cheap talk: {cheap_talk}
Costly signaling bypass: {costly_signaling_bypass}
Domain: {domain}
Context: {context}

Are screening mechanisms failing to identify information quality? Return ONLY valid JSON."""


class EpistemicInformationAsymmetryScreeningFailureService:
    """Detects epistemic information asymmetry screening failure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        quality_signal_failure: str,
        *,
        credential_inflation: str = "",
        cheap_talk: str = "",
        costly_signaling_bypass: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic information asymmetry screening failure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFORMATION_ASYMMETRY_SCREENING_FAILURE_PROMPT.format(
                quality_signal_failure=quality_signal_failure,
                credential_inflation=credential_inflation or "Not specified",
                cheap_talk=cheap_talk or "Not specified",
                costly_signaling_bypass=costly_signaling_bypass or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFORMATION_ASYMMETRY_SCREENING_FAILURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "quality_signal_failure": quality_signal_failure[:200],
            "screening_failure_detected": data.get("screening_failure_detected", False),
            "severity": data.get("severity", ""),
            "credential_inflation": data.get("credential_inflation", ""),
            "cheap_talk": data.get("cheap_talk", ""),
            "costly_signaling_bypass": data.get("costly_signaling_bypass", ""),
            "recommendation": data.get("recommendation", ""),
        }
