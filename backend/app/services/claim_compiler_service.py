"""ClaimCompilerService — Paper-to-Claim Compiler.

Turns raw paper text (title + abstract + chunks) into ledger-ready atomic claims
using LLM extraction followed by atomic validation.
"""

import json
import re
import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXTRACTION_SYSTEM = """You are a scientific claim extractor. Given a paper's text, extract ALL distinct empirical claims.

Rules:
- Each claim must be a single, atomic, falsifiable statement
- Each claim must be 25-200 characters
- Do NOT include meta-statements about the paper itself ("this paper shows...", "we propose...")
- Do NOT include vague or unfalsifiable claims
- Extract the specific quantitative or qualitative findings
- Include methodology context when it strengthens the claim (e.g., "in a randomized trial of N=500...")
- Preserve the original meaning — do not editorialize

Output JSON with this exact structure:
{
  "claims": [
    {
      "text": "the atomic claim text",
      "evidence_type": "experimental|observational|theoretical|meta_analysis|benchmark|anecdotal",
      "confidence": 0.0-1.0,
      "source_span": "brief quote from source that supports this claim"
    }
  ]
}"""

EXTRACTION_PROMPT_TEMPLATE = """Extract all distinct empirical claims from this paper text:

---
{text}
---

Return ONLY valid JSON. Extract 1-10 claims. Focus on the most important, specific, falsifiable findings."""


@dataclass
class CompilationResult:
    paper_text: str
    candidates_extracted: int
    candidates_validated: int
    candidates_rejected: int
    claims_merged: int
    claims_new: int
    claim_ids: list[str]
    rejected_reasons: list[str]


class ClaimCompilerService:
    """Extracts atomic claims from paper text and writes them to the ledger."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_paper(
        self,
        text: str,
        *,
        dossier_id: str | None = None,
        source_tool: str = "claim_compiler",
        paper_id: str | None = None,
        max_claims: int = 10,
    ) -> dict:
        """Full pipeline: extract → validate → deduplicate → write to ledger."""
        from app.clients.llm_client import LLMClient
        from app.services.claim_ledger_service import ClaimLedgerService

        llm = LLMClient()
        ledger = ClaimLedgerService(self.db)

        truncated = text[:6000]

        try:
            raw_response = await llm.complete(
                prompt=EXTRACTION_PROMPT_TEMPLATE.format(text=truncated),
                system=EXTRACTION_SYSTEM,
                max_tokens=2048,
                temperature=0.1,
            )
            extraction = self._parse_json_robust(raw_response)
        except Exception as e:
            logger.error("claim_extraction_failed", error=str(e))
            return {"error": f"LLM extraction failed: {str(e)}", "claims": []}

        raw_claims = extraction.get("claims", [])
        if not raw_claims:
            return {
                "candidates_extracted": 0,
                "candidates_validated": 0,
                "claims_new": 0,
                "claims_merged": 0,
                "claim_ids": [],
            }

        raw_claims = raw_claims[:max_claims]
        candidates_extracted = len(raw_claims)

        claim_ids = []
        validated = 0
        rejected = 0
        merged = 0
        new = 0
        rejected_reasons = []

        for raw in raw_claims:
            claim_text = raw.get("text", "").strip()
            if not claim_text:
                continue

            confidence = raw.get("confidence")
            evidence_type = raw.get("evidence_type", "unknown")

            result = await ledger.upsert_claim(
                text=claim_text,
                dossier_id=dossier_id,
                source_tool=source_tool,
                confidence=confidence,
                metadata={
                    "evidence_type": evidence_type,
                    "source_span": raw.get("source_span", ""),
                    "paper_id": paper_id,
                    "compiled": True,
                },
            )

            if result.get("error"):
                rejected += 1
                rejected_reasons.append(f"{claim_text[:50]}... → {result['error']}")
                continue

            claims = result.get("claims", [])
            if claims:
                validated += len(claims)
                for c in claims:
                    cid = c.get("claim_id") or c.get("global_claim_id")
                    if cid:
                        claim_ids.append(str(cid))
                    if c.get("action") == "merged":
                        merged += 1
                    else:
                        new += 1
            elif result.get("claim_id") or result.get("global_claim_id"):
                validated += 1
                cid = result.get("claim_id") or result.get("global_claim_id")
                claim_ids.append(str(cid))
                if result.get("action") == "merged":
                    merged += 1
                else:
                    new += 1

        return {
            "candidates_extracted": candidates_extracted,
            "candidates_validated": validated,
            "candidates_rejected": rejected,
            "claims_new": new,
            "claims_merged": merged,
            "claim_ids": claim_ids,
            "rejected_reasons": rejected_reasons[:5],
            "yield_rate": round(validated / max(1, candidates_extracted), 2),
        }

    async def compile_from_openalex(
        self,
        paper: dict,
        *,
        dossier_id: str | None = None,
    ) -> dict:
        """Compile claims from an OpenAlex paper record."""
        title = paper.get("title", "")
        abstract = paper.get("abstract_inverted_index") or paper.get("abstract", "")

        if isinstance(abstract, dict):
            words = sorted(abstract.items(), key=lambda x: x[1][0] if x[1] else 0)
            abstract = " ".join(w[0] for w in words)

        if not title and not abstract:
            return {"error": "No text to extract from", "claims": []}

        text = f"Title: {title}\n\nAbstract: {abstract}"
        openalex_id = paper.get("id", "")

        return await self.compile_paper(
            text,
            dossier_id=dossier_id,
            source_tool="openalex_compiler",
            paper_id=openalex_id,
        )

    async def compile_batch(
        self,
        papers: list[dict],
        *,
        dossier_id: str | None = None,
        max_papers: int = 5,
    ) -> dict:
        """Compile claims from multiple papers."""
        papers = papers[:max_papers]
        total_extracted = 0
        total_validated = 0
        total_rejected = 0
        total_new = 0
        total_merged = 0
        all_claim_ids = []

        for paper in papers:
            result = await self.compile_from_openalex(paper, dossier_id=dossier_id)
            if result.get("error"):
                continue
            total_extracted += result.get("candidates_extracted", 0)
            total_validated += result.get("candidates_validated", 0)
            total_rejected += result.get("candidates_rejected", 0)
            total_new += result.get("claims_new", 0)
            total_merged += result.get("claims_merged", 0)
            all_claim_ids.extend(result.get("claim_ids", []))

        return {
            "papers_processed": len(papers),
            "candidates_extracted": total_extracted,
            "candidates_validated": total_validated,
            "candidates_rejected": total_rejected,
            "claims_new": total_new,
            "claims_merged": total_merged,
            "claim_ids": all_claim_ids,
            "yield_rate": round(total_validated / max(1, total_extracted), 2),
        }

    def _parse_json_robust(self, text: str) -> dict:
        """Parse JSON from LLM output, handling common malformations."""
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Extract JSON block from markdown fences
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                text = fence_match.group(1).strip()

        # Find the outermost { ... } block
        start = text.find("{")
        if start == -1:
            return {"claims": []}

        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        candidate = text[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Try fixing trailing commas and truncated strings
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
        # Close any unclosed strings/arrays/objects
        open_braces = fixed.count("{") - fixed.count("}")
        open_brackets = fixed.count("[") - fixed.count("]")
        if open_brackets > 0:
            fixed += "]" * open_brackets
        if open_braces > 0:
            fixed += "}" * open_braces

        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Last resort: regex extract claim texts
        claim_texts = re.findall(r'"text"\s*:\s*"([^"]{25,200})"', text)
        if claim_texts:
            return {"claims": [{"text": t, "evidence_type": "unknown", "confidence": 0.5} for t in claim_texts]}

        return {"claims": []}
