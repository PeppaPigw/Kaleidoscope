"""ResearchCompilerService — Intelligence-to-Output Compiler.

Takes raw research intelligence from all engines and compiles it into
structured, actionable output formats: research briefs, executive summaries,
gap analyses, and research proposals. The output layer of the platform.
"""

import uuid
from datetime import datetime, timezone

import structlog

from app.services.llm_utils import parse_llm_json
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BRIEF_SYSTEM = """You are a research intelligence compiler. Given raw research data from multiple analytical engines, compile it into a structured research brief that a decision-maker can act on.

The brief should be: precise, actionable, honest about uncertainty, and structured for quick scanning.

Output JSON with: brief.title, brief.executive_summary (3 sentences max), brief.confidence_level (0-1), brief.key_findings (list of finding/confidence/source/actionability), brief.open_questions (list ranked by importance), brief.risks (list of risk/probability/impact/mitigation), brief.recommended_actions (list of action/priority/rationale/effort), brief.knowledge_gaps (list), brief.next_steps (ordered list), brief.meta (total_sources/analysis_depth/blind_spots_identified)."""

BRIEF_PROMPT = """Compile a research brief from this intelligence:

Research question: {question}
Domain: {domain}

Claims and evidence:
{claims_text}

Synthesis findings:
{synthesis_text}

Adversarial assessment:
{adversarial_text}

Blind spots identified:
{blind_spots_text}

Confidence assessment:
{confidence_text}

Compile into an actionable research brief. Return ONLY valid JSON."""

PROPOSAL_SYSTEM = """You are a research proposal compiler. Given a research question and the current state of knowledge (including gaps, blind spots, and open questions), generate a structured research proposal that addresses the most important unknowns.

Output JSON with: proposal.title, proposal.abstract (150 words max), proposal.motivation (why this matters now), proposal.research_questions (ordered list), proposal.methodology (list of method/rationale/limitations), proposal.expected_contributions (list), proposal.timeline (list of phase/duration/deliverable), proposal.risks_and_mitigations (list), proposal.success_criteria (list of criterion/measurement), proposal.novelty_claim (what's new about this approach), proposal.estimated_impact (0-1)."""

PROPOSAL_PROMPT = """Generate a research proposal:

Domain: {domain}
Core question: {question}

Current knowledge state:
{knowledge_text}

Identified gaps:
{gaps_text}

Blind spots to address:
{blind_spots_text}

Failed approaches:
{failed_text}

Generate a research proposal that addresses the most important unknowns. Return ONLY valid JSON."""

GAP_ANALYSIS_SYSTEM = """You are a research gap analyst. Given the current state of knowledge, identify and prioritize the gaps - what we need to know but don't yet. Distinguish between gaps that are addressable (we could fill them with effort) and gaps that are structural (require new methods or paradigms).

Output JSON with: gap_analysis.total_gaps, gap_analysis.addressable_gaps (list of gap/importance/effort_to_fill/method_to_fill/blocking), gap_analysis.structural_gaps (list of gap/why_structural/what_would_change_this), gap_analysis.priority_ranking (ordered list of gap ids), gap_analysis.critical_path (the minimum set of gaps to fill for progress), gap_analysis.low_hanging_fruit (easiest gaps with highest value), gap_analysis.research_debt (accumulated unfilled gaps that compound)."""

GAP_ANALYSIS_PROMPT = """Analyze research gaps:

Domain: {domain}
Question: {question}

What we know:
{known_text}

What we've tried:
{tried_text}

What remains uncertain:
{uncertain_text}

Identify and prioritize the gaps. Return ONLY valid JSON."""


class ResearchCompilerService:
    """Compiles research intelligence into actionable outputs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_brief(
        self,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Compile a full research brief from all available intelligence."""
        from app.clients.llm_client import LLMClient

        claims = await self._gather_claims(question, dossier_id)
        claims_text = "\n".join(f"- {c}" for c in claims[:10]) or "Limited claims"

        synthesis_text = await self._get_synthesis(question, dossier_id)
        adversarial_text = await self._get_adversarial(question, claims)
        blind_spots_text = await self._get_blind_spots(question, domain)
        confidence_text = await self._get_confidence(claims)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BRIEF_PROMPT.format(
                question=question,
                domain=domain or "research",
                claims_text=claims_text,
                synthesis_text=synthesis_text,
                adversarial_text=adversarial_text,
                blind_spots_text=blind_spots_text,
                confidence_text=confidence_text,
            ),
            system=BRIEF_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        brief = data.get("brief", data)

        return {
            "title": brief.get("title", question[:60]),
            "executive_summary": brief.get("executive_summary", ""),
            "confidence_level": brief.get("confidence_level", 0),
            "key_findings": brief.get("key_findings", []),
            "open_questions": brief.get("open_questions", []),
            "risks": brief.get("risks", []),
            "recommended_actions": brief.get("recommended_actions", []),
            "knowledge_gaps": brief.get("knowledge_gaps", []),
            "next_steps": brief.get("next_steps", []),
            "meta": brief.get("meta", {}),
        }

    async def generate_proposal(
        self,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Generate a research proposal addressing key unknowns."""
        from app.clients.llm_client import LLMClient

        knowledge = await self._gather_claims(question, dossier_id)
        knowledge_text = "\n".join(f"- {k}" for k in knowledge[:8]) or "Limited"

        gaps = await self._get_gaps(question, dossier_id)
        gaps_text = "\n".join(f"- {g}" for g in gaps[:6]) or "Gaps not characterized"
        blind_spots_text = await self._get_blind_spots(question, domain)
        failed_text = await self._get_failed(dossier_id)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROPOSAL_PROMPT.format(
                domain=domain or "research",
                question=question,
                knowledge_text=knowledge_text,
                gaps_text=gaps_text,
                blind_spots_text=blind_spots_text,
                failed_text=failed_text,
            ),
            system=PROPOSAL_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        proposal = data.get("proposal", data)

        return {
            "title": proposal.get("title", ""),
            "abstract": proposal.get("abstract", ""),
            "motivation": proposal.get("motivation", ""),
            "research_questions": proposal.get("research_questions", []),
            "methodology": proposal.get("methodology", []),
            "expected_contributions": proposal.get("expected_contributions", []),
            "timeline": proposal.get("timeline", []),
            "risks": proposal.get("risks_and_mitigations", []),
            "success_criteria": proposal.get("success_criteria", []),
            "novelty_claim": proposal.get("novelty_claim", ""),
            "estimated_impact": proposal.get("estimated_impact", 0),
        }

    async def analyze_gaps(
        self,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Identify and prioritize research gaps."""
        from app.clients.llm_client import LLMClient

        known = await self._gather_claims(question, dossier_id)
        known_text = "\n".join(f"- {k}" for k in known[:10]) or "Limited"
        tried_text = await self._get_failed(dossier_id)
        uncertain = await self._get_gaps(question, dossier_id)
        uncertain_text = "\n".join(f"- {u}" for u in uncertain[:8]) or "Not characterized"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=GAP_ANALYSIS_PROMPT.format(
                domain=domain or "research",
                question=question,
                known_text=known_text,
                tried_text=tried_text,
                uncertain_text=uncertain_text,
            ),
            system=GAP_ANALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        analysis = data.get("gap_analysis", data)

        return {
            "question": question,
            "total_gaps": analysis.get("total_gaps", 0),
            "addressable_gaps": analysis.get("addressable_gaps", []),
            "structural_gaps": analysis.get("structural_gaps", []),
            "priority_ranking": analysis.get("priority_ranking", []),
            "critical_path": analysis.get("critical_path", []),
            "low_hanging_fruit": analysis.get("low_hanging_fruit", []),
            "research_debt": analysis.get("research_debt", ""),
        }

    # --- Private intelligence gatherers ---

    async def _gather_claims(self, query: str, dossier_id: str | None) -> list[str]:
        claims = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier and dossier.claims:
                    for c in dossier.claims[:12]:
                        if isinstance(c, dict):
                            claims.append(c.get("text", c.get("claim", str(c)))[:200])
                        else:
                            claims.append(str(c)[:200])
            except Exception:
                pass
        if not claims:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=query[:150], top_k=8)
                for r in results:
                    p = r.get("payload", {})
                    claims.append(p.get("text", p.get("title", ""))[:200])
            except Exception:
                pass
        return claims

    async def _get_synthesis(self, question: str, dossier_id: str | None) -> str:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{question[:80]} synthesis convergence", top_k=3)
            lines = [r.get("payload", {}).get("text", "")[:100] for r in results]
            return "\n".join(f"- {l}" for l in lines if l) or "No synthesis available"
        except Exception:
            return "Synthesis not available"

    async def _get_adversarial(self, question: str, claims: list[str]) -> str:
        if not claims:
            return "No adversarial assessment"
        top_claim = claims[0] if claims else question
        return f"Top claim to stress-test: {top_claim[:100]}"

    async def _get_blind_spots(self, question: str, domain: str) -> str:
        return f"Blind spot analysis pending for: {question[:80]} in {domain or 'general'}"

    async def _get_confidence(self, claims: list[str]) -> str:
        return f"{len(claims)} claims available, confidence assessment pending"

    async def _get_gaps(self, question: str, dossier_id: str | None) -> list[str]:
        gaps = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier and dossier.gaps:
                    for g in dossier.gaps[:8]:
                        if isinstance(g, dict):
                            gaps.append(g.get("text", g.get("gap", str(g)))[:150])
                        else:
                            gaps.append(str(g)[:150])
            except Exception:
                pass
        return gaps

    async def _get_failed(self, dossier_id: str | None) -> str:
        if not dossier_id:
            return "No failed approaches recorded"
        try:
            from app.models.dossier import ResearchDossier
            from sqlalchemy import select
            stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
            result = await self.db.execute(stmt)
            dossier = result.scalar_one_or_none()
            if dossier and dossier.failed_searches:
                return "\n".join(f"- {f}" for f in dossier.failed_searches[:5])
        except Exception:
            pass
        return "No failed approaches recorded"
