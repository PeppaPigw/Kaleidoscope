"""EvidenceChainService — Evidence Chain Validator.

Traces evidence chains from a claim back to primary sources, checking
each link for validity, transformation fidelity, and potential distortion.
Identifies where evidence degrades, gets misquoted, or loses context as
it passes through citation chains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRACE_SYSTEM = """You are an evidence chain analyst. Given a claim and its supporting evidence, trace the chain of evidence back toward primary sources. For each link in the chain, assess:
- Source type (primary data, meta-analysis, review, commentary, media report, etc.)
- Transformation fidelity: how accurately does this link represent its source?
- Context preservation: is important context maintained or stripped?
- Potential distortion: where might meaning have shifted?

Output JSON with: chain (list of links, each with: level (0=claim, 1=direct citation, 2=citation's source, etc.), source_type, description, fidelity_score (0-1), context_preserved (bool), distortion_risk, notes), overall_chain_strength (0-1), weakest_link (which level and why), primary_source_reached (bool), recommendations (list of verification steps)."""

TRACE_PROMPT = """Trace the evidence chain for this claim:

Claim: {claim}
Domain: {domain}

Supporting evidence provided:
{evidence_text}

Trace back toward primary sources, assessing each link. Return ONLY valid JSON."""

VERIFY_SYSTEM = """You are an evidence verification specialist. Given a specific link in an evidence chain, perform deep verification. Check:
- Does the cited source actually say what's claimed?
- Is the interpretation reasonable or stretched?
- Are there known retractions, corrections, or contradictions?
- What would strengthen or weaken this link?

Output JSON with: link_assessment.source_claim_match (0-1), link_assessment.interpretation_quality (conservative/reasonable/stretched/misrepresented), link_assessment.known_issues (list), link_assessment.strengthening_evidence (list), link_assessment.weakening_evidence (list), link_assessment.verdict (strong/adequate/weak/broken), link_assessment.confidence (0-1)."""

VERIFY_PROMPT = """Verify this evidence chain link:

Original claim: {claim}
Link being verified: {link_description}
Source type: {source_type}
Context: {context}

Assess whether this link faithfully represents its source. Return ONLY valid JSON."""


class EvidenceChainService:
    """Traces and validates evidence chains from claims to primary sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def trace_chain(
        self,
        claim: str,
        *,
        evidence: list[str] | None = None,
        domain: str = "",
    ) -> dict:
        """Trace an evidence chain from claim back to primary sources."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        context_evidence = await self._gather_evidence(claim)
        all_evidence = (evidence or []) + context_evidence
        evidence_text = "\n".join(f"- {e}" for e in all_evidence[:10]) or "No direct evidence provided — infer likely chain"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRACE_PROMPT.format(
                claim=claim,
                domain=domain or "research",
                evidence_text=evidence_text,
            ),
            system=TRACE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        chain = data.get("chain", [])
        return {
            "claim": claim,
            "chain_length": len(chain),
            "chain": chain,
            "overall_strength": data.get("overall_chain_strength", 0),
            "weakest_link": data.get("weakest_link", ""),
            "primary_reached": data.get("primary_source_reached", False),
            "recommendations": data.get("recommendations", []),
        }

    async def verify_link(
        self,
        claim: str,
        link_description: str,
        *,
        source_type: str = "",
        context: str = "",
    ) -> dict:
        """Deep-verify a specific link in an evidence chain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=VERIFY_PROMPT.format(
                claim=claim,
                link_description=link_description,
                source_type=source_type or "unknown",
                context=context or "No additional context",
            ),
            system=VERIFY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        assessment = data.get("link_assessment", data)

        return {
            "claim": claim,
            "link": link_description,
            "source_claim_match": assessment.get("source_claim_match", 0),
            "interpretation": assessment.get("interpretation_quality", ""),
            "known_issues": assessment.get("known_issues", []),
            "strengthening": assessment.get("strengthening_evidence", []),
            "weakening": assessment.get("weakening_evidence", []),
            "verdict": assessment.get("verdict", ""),
            "confidence": assessment.get("confidence", 0),
        }

    async def _gather_evidence(self, claim: str) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=claim[:100], top_k=5)
            return [r.get("payload", {}).get("text", "")[:150] for r in results if r.get("payload", {}).get("text")]
        except Exception:
            return []
