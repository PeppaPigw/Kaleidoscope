"""EpistemicErrorCorrectionService — Epistemic Error Correction Detection.

Detects epistemic error correction — intellectual redundancy enabling
detection and correction of corrupted ideas during transmission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ERROR_CORRECTION_SYSTEM = """You are an epistemic error correction specialist. Given an intellectual transmission, assess whether redundancy enables corruption detection and correction:

Key concepts:
- Epistemic error correction: redundancy enabling corruption repair
- Parity check: detecting single errors
- Hamming distance: minimum differences between valid states
- Checksum: summary verifying integrity
- Forward error correction: correcting without retransmission
- Interleaving: spreading errors across codewords
- Turbo code: iterative decoding approaching capacity

When epistemic error correction IS present:
- Redundancy enabling detection of corrupted ideas
- Single errors detectable through parity
- Sufficient distance between valid intellectual states
- Summary checks verifying idea integrity
- Correction possible without re-asking
- Errors spread to prevent burst corruption
- Iterative refinement approaching perfect correction

When uncorrected transmission is present:
- No redundancy for error detection
- Errors undetectable
- Valid states too close together
- No integrity verification
- Must retransmit on any error
- Burst errors destroying entire messages
- No iterative improvement

Output JSON with: error_correction_present (bool), severity (none/mild/moderate/severe), parity (what detection), hamming (what distance), checksum (what verification), forward_correction (what repair method), recommendation (uncorrected_transmission/mild_correction/significant_error_correction/major_redundancy_coding/optimize_hamming_distance)."""

EPISTEMIC_ERROR_CORRECTION_PROMPT = """Detect epistemic error correction:

Parity: {parity}
Hamming: {hamming}
Checksum: {checksum}
Forward correction: {forward_correction}
Domain: {domain}
Context: {context}

Is intellectual redundancy enabling detection and correction of corrupted ideas during transmission? Return ONLY valid JSON."""


class EpistemicErrorCorrectionService:
    """Detects epistemic error correction — redundancy enabling repair."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        parity: str,
        *,
        hamming: str = "",
        checksum: str = "",
        forward_correction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic error correction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ERROR_CORRECTION_PROMPT.format(
                parity=parity,
                hamming=hamming or "Not specified",
                checksum=checksum or "Not specified",
                forward_correction=forward_correction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ERROR_CORRECTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "parity": parity[:200],
            "error_correction_present": data.get("error_correction_present", False),
            "severity": data.get("severity", ""),
            "hamming": data.get("hamming", ""),
            "checksum": data.get("checksum", ""),
            "forward_correction": data.get("forward_correction", ""),
            "recommendation": data.get("recommendation", ""),
        }
