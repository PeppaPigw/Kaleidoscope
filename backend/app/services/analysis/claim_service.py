"""Claim extraction service — LLM-powered atomic claim and evidence extraction.

P3 WS-1: §17 (#129-140) from FeasibilityAnalysis.md

MVP scope (following the doc's advice):
- LLM extract core claims from a paper
- Simple evidence-passage location
- Claim classification (type + hedging)
- Evidence sufficiency assessment

Deferred to V2: cross-paper alignment, consensus/divergence detection.
"""

import json

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, EvidenceLink
from app.models.paper import Paper

logger = structlog.get_logger(__name__)

# ─── Prompt Templates ────────────────────────────────────────────

CLAIM_EXTRACTION_PROMPT = """Extract all atomic claims from this academic paper.

**Title**: {title}
**Abstract**: {abstract}
**Text**: {text}

An "atomic claim" is a single, specific, falsifiable or verifiable statement.

For each claim, provide:
1. text: the exact claim statement (1-2 sentences)
2. claim_type: one of [contribution, finding, hypothesis, assumption, limitation]
3. category: one of [architectural, methodological, theoretical, empirical, application]
4. hedging_level: how certain is the language? [strong, moderate, weak]
   - strong: "we demonstrate", "our method achieves"
   - moderate: "the results suggest", "we observe that"
   - weak: "it may be possible", "we hypothesize"
5. section_ref: which section the claim appears in (e.g., "Introduction", "Results §3.2")
6. evidence: [ {{
     "evidence_type": "text" | "figure" | "table" | "reference" | "data",
     "evidence_text": relevant supporting text (1-3 sentences),
     "location": where the evidence is (e.g., "Table 3", "Section 4.2"),
     "strength": "strong" | "moderate" | "weak" | "insufficient"
   }} ]

Return JSON array:
[{{
    "text": "...",
    "claim_type": "...",
    "category": "...",
    "hedging_level": "...",
    "section_ref": "...",
    "evidence": [...]
}}]

Focus on the most important claims (up to 15). Prioritize novel contributions.
Return ONLY the JSON array."""

EVIDENCE_ASSESSMENT_PROMPT = """Assess whether the evidence provided in this paper actually supports its key claims.

**Title**: {title}
**Claims and evidence**:
{claims_json}

For each claim, evaluate:
1. Is the evidence sufficient? (true/false)
2. What type of additional evidence would strengthen it?
3. Are there potential confounders or alternative explanations?

Return JSON:
[{{
    "claim_index": 0,
    "is_sufficient": true,
    "gaps": ["missing ablation study", "no error bars"],
    "alternative_explanations": ["could be due to data leakage"]
}}]

Return ONLY the JSON array."""


class ClaimExtractionService:
    """Extract and manage atomic claims from papers."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm(self):
        if self._llm_client is None:
            from app.clients.llm_client import LLMClient

            self._llm_client = LLMClient()
        return self._llm_client

    async def _get_paper_text(self, paper_id: str) -> tuple[Paper, str]:
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")

        parts = []
        if paper.abstract:
            parts.append(paper.abstract)
        if paper.parsed_sections:
            for sec in paper.parsed_sections:
                if sec.get("title"):
                    parts.append(f"\n## {sec['title']}\n")
                for p in sec.get("paragraphs", []):
                    parts.append(p)
        elif paper.raw_metadata and paper.raw_metadata.get("parsed_sections"):
            for sec in paper.raw_metadata["parsed_sections"]:
                if sec.get("title"):
                    parts.append(f"\n## {sec['title']}\n")
                for p in sec.get("paragraphs", []):
                    parts.append(p)

        text = "\n".join(parts)
        if len(text) > 15000:
            text = text[:15000] + "\n[... truncated ...]"
        return paper, text

    async def extract_claims(self, paper_id: str) -> dict:
        """
        Extract atomic claims from a paper.

        Idempotent: deletes any previous claims for this paper before inserting.
        Returns claims with evidence links, persistently stored.
        """
        log = logger.bind(paper_id=paper_id)
        paper, text = await self._get_paper_text(paper_id)

        # --- Idempotent: remove prior extraction for this paper ---
        old_claims = await self.db.execute(
            select(Claim).where(Claim.paper_id == paper_id)
        )
        for old in old_claims.scalars().all():
            # CASCADE delete-orphan removes EvidenceLink rows
            await self.db.delete(old)
        await self.db.flush()

        llm = await self._get_llm()
        prompt = CLAIM_EXTRACTION_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract or "",
            text=text,
        )

        try:
            response = await llm.complete(
                prompt=prompt, temperature=0.2, max_tokens=4096
            )
            raw_claims = json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            log.error("claim_extraction_failed", error=str(e))
            return {"paper_id": paper_id, "claims": [], "error": str(e)}

        # Persist claims and evidence
        stored_claims = []
        for i, rc in enumerate(raw_claims):
            claim = Claim(
                paper_id=paper_id,
                text=rc.get("text", ""),
                claim_type=rc.get("claim_type"),
                category=rc.get("category"),
                hedging_level=rc.get("hedging_level"),
                section_ref=rc.get("section_ref"),
                position=i,
                confidence=0.8,  # default LLM confidence
                source="llm",
            )
            self.db.add(claim)
            await self.db.flush()

            # Store evidence links
            for ev in rc.get("evidence", []):
                link = EvidenceLink(
                    claim_id=str(claim.id),
                    paper_id=paper_id,
                    evidence_type=ev.get("evidence_type", "text"),
                    evidence_text=ev.get("evidence_text"),
                    location=ev.get("location"),
                    strength=ev.get("strength"),
                )
                self.db.add(link)

            stored_claims.append(
                {
                    "id": str(claim.id),
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "category": claim.category,
                    "hedging_level": claim.hedging_level,
                    "section_ref": claim.section_ref,
                    "evidence_count": len(rc.get("evidence", [])),
                }
            )

        await self.db.commit()
        log.info("claims_extracted", count=len(stored_claims))

        return {
            "paper_id": paper_id,
            "title": paper.title,
            "claims": stored_claims,
        }

    async def list_claims(self, paper_id: str) -> list[dict]:
        """List all claims for a paper."""
        result = await self.db.execute(
            select(Claim).where(Claim.paper_id == paper_id).order_by(Claim.position)
        )
        claims = result.scalars().all()

        output = []
        for c in claims:
            ev_result = await self.db.execute(
                select(EvidenceLink).where(EvidenceLink.claim_id == str(c.id))
            )
            evidence = ev_result.scalars().all()
            output.append(
                {
                    "id": str(c.id),
                    "text": c.text,
                    "claim_type": c.claim_type,
                    "category": c.category,
                    "hedging_level": c.hedging_level,
                    "section_ref": c.section_ref,
                    "confidence": c.confidence,
                    "evidence": [
                        {
                            "type": e.evidence_type,
                            "text": e.evidence_text,
                            "location": e.location,
                            "strength": e.strength,
                            "is_sufficient": e.is_sufficient,
                            "gaps": (e.metadata_json or {}).get("gaps", []),
                            "alternative_explanations": (e.metadata_json or {}).get(
                                "alternative_explanations", []
                            ),
                        }
                        for e in evidence
                    ],
                }
            )
        return output

    async def assess_evidence(self, paper_id: str) -> dict:
        """
        Assess evidence sufficiency for all claims in a paper.

        Persists is_sufficient and assessment metadata back to EvidenceLink rows.
        """
        claims_data = await self.list_claims(paper_id)
        if not claims_data:
            return {"paper_id": paper_id, "assessments": [], "error": "No claims found"}

        paper, _ = await self._get_paper_text(paper_id)
        llm = await self._get_llm()

        claims_json = json.dumps(claims_data[:10], indent=2, ensure_ascii=False)
        prompt = EVIDENCE_ASSESSMENT_PROMPT.format(
            title=paper.title,
            claims_json=claims_json,
        )

        try:
            response = await llm.complete(prompt=prompt, temperature=0.2)
            assessments = json.loads(response)
        except Exception as e:
            logger.error("evidence_assessment_failed", error=str(e))
            return {"paper_id": paper_id, "assessments": [], "error": str(e)}

        # Persist assessment back to EvidenceLink rows
        for assessment in assessments:
            claim_idx = assessment.get("claim_index", -1)
            if claim_idx < 0 or claim_idx >= len(claims_data):
                continue

            claim_id = claims_data[claim_idx]["id"]
            is_sufficient = assessment.get("is_sufficient", None)
            assessment_meta = {
                "gaps": assessment.get("gaps", []),
                "alternative_explanations": assessment.get(
                    "alternative_explanations", []
                ),
            }

            # Update all evidence links for this claim
            ev_result = await self.db.execute(
                select(EvidenceLink).where(EvidenceLink.claim_id == claim_id)
            )
            for link in ev_result.scalars().all():
                link.is_sufficient = is_sufficient
                link.metadata_json = assessment_meta

        await self.db.commit()
        logger.info(
            "evidence_assessment_persisted", paper_id=paper_id, count=len(assessments)
        )

        return {
            "paper_id": paper_id,
            "title": paper.title,
            "assessments": assessments,
        }

    async def close(self):
        if self._llm_client:
            try:
                await self._llm_client.close()
            except Exception:
                pass
