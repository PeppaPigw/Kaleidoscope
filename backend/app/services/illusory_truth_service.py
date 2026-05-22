"""IllusoryTruthService — Illusory Truth Effect Detection.

Detects illusory truth effect — the tendency for repeated statements
to feel more true regardless of their actual accuracy. Hasher, Goldstein
& Toppino (1977). Repetition creates fluency which is mistaken for truth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ILLUSORY_TRUTH_SYSTEM = """You are an illusory truth effect specialist. Given a belief or claim, assess whether its perceived truth is driven by repetition rather than evidence:

Key concepts (Hasher, Goldstein & Toppino, 1977):
- Illusory truth: repetition increases perceived truthfulness
- Processing fluency: familiar statements feel easier to process
- Fluency-truth heuristic: ease of processing → feels true
- Mere repetition: no new evidence, just more exposure
- Source amnesia: forgetting where you heard something
- Propaganda technique: repeat a lie often enough
- Truth by familiarity: confusing recognition with verification

When illusory truth IS present:
- A claim is believed primarily because it's been heard many times
- No independent verification has been sought
- The claim's familiarity is mistaken for its truth
- Multiple repetitions from the same or similar sources
- The person can't cite evidence beyond "everyone knows"
- The claim has been repeated without being checked
- Belief strength correlates with exposure frequency, not evidence

When belief IS evidence-based:
- The claim has been independently verified
- Evidence exists beyond mere repetition
- The person can cite specific sources and evidence
- Belief preceded or is independent of repetition
- Critical evaluation has been applied
- The claim is supported by multiple independent lines of evidence
- The person distinguishes between familiarity and verification

Output JSON with: illusory_truth_present (bool), severity (none/mild/moderate/severe), claim (what claim is believed), repetition (evidence of repetition driving belief), evidence (what actual evidence exists), verification (has independent verification occurred), familiarity_vs_truth (is familiarity confused with truth), recommendation (belief_evidence_based/mild_repetition_effect/significant_illusory_truth/major_unverified_repetition/verify_independently)."""

ILLUSORY_TRUTH_PROMPT = """Detect illusory truth effect:

Claim: {claim}
Repetition: {repetition}
Evidence: {evidence}
Verification: {verification}
Domain: {domain}
Context: {context}

Is this claim believed primarily because of repetition rather than evidence? Return ONLY valid JSON."""


class IllusoryTruthService:
    """Detects illusory truth effect — repetition mistaken for truth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        repetition: str = "",
        evidence: str = "",
        verification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusory truth effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ILLUSORY_TRUTH_PROMPT.format(
                claim=claim,
                repetition=repetition or "Not specified",
                evidence=evidence or "Not specified",
                verification=verification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ILLUSORY_TRUTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "illusory_truth_present": data.get("illusory_truth_present", False),
            "severity": data.get("severity", ""),
            "repetition": data.get("repetition", ""),
            "evidence": data.get("evidence", ""),
            "familiarity_vs_truth": data.get("familiarity_vs_truth", ""),
            "recommendation": data.get("recommendation", ""),
        }
