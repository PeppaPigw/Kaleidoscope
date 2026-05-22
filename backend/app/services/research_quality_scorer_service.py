"""ResearchQualityScorerService — Unified Quality Assessment.

Combines multiple quality dimensions into a single actionable score.
Evaluates research across: methodology rigor, evidence strength, logical
coherence, novelty, reproducibility, and practical impact. Produces both
a composite score and dimensional breakdown with specific improvement actions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SCORE_SYSTEM = """You are a research quality assessor. Evaluate research across 8 dimensions, each scored 0-1:

1. Methodology Rigor: design quality, controls, sample adequacy
2. Evidence Strength: effect sizes, replication, convergence
3. Logical Coherence: argument validity, no fallacies, sound inferences
4. Novelty: originality, non-obvious contributions
5. Reproducibility: methods clarity, data availability, code sharing
6. Practical Impact: actionability, real-world applicability
7. Transparency: limitations acknowledged, conflicts disclosed, pre-registration
8. Robustness: sensitivity to assumptions, alternative explanations addressed

Output JSON with: quality.overall_score (0-1 weighted composite), quality.grade (A+|A|B+|B|C+|C|D|F), quality.dimensions (list of dimension/score 0-1/weight/evidence/weaknesses), quality.critical_flaws (list of flaw/dimension/how_it_undermines), quality.strengths (list), quality.improvement_actions (ordered list of action/dimension/expected_improvement/effort low|medium|high), quality.comparison_percentile (estimated percentile vs field average), quality.publication_readiness (ready|minor_revisions|major_revisions|not_ready)."""

SCORE_PROMPT = """Score research quality:

Title/Topic: {topic}
Claims: {claims_text}
Methodology: {methodology}
Evidence: {evidence_text}
Domain: {domain}

Score across all 8 dimensions. Return ONLY valid JSON."""

BENCHMARK_SYSTEM = """You are a research benchmarking expert. Given a piece of research and its domain, compare it against field standards and exemplars. Where does it sit relative to the best and worst in the field?

Output JSON with: benchmark.topic, benchmark.field_position (top_1_percent|top_10|above_average|average|below_average|bottom_quartile), benchmark.compared_to (list of exemplar/their_score/how_this_compares), benchmark.field_standards (list of standard/this_research_meets_it bool/gap), benchmark.what_top_papers_do_differently (list), benchmark.achievable_improvements (list of improvement/effort/impact)."""

BENCHMARK_PROMPT = """Benchmark this research against field standards:

Research: {research}
Domain: {domain}
Key claims: {claims_text}

Compare against field standards. Return ONLY valid JSON."""


class ResearchQualityScorerService:
    """Unified research quality scoring across multiple dimensions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def score(
        self,
        topic: str,
        *,
        claims: list[str] | None = None,
        methodology: str = "",
        evidence: list[str] | None = None,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Score research quality across 8 dimensions."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(f"- {c}" for c in (claims or [])[:6]) or "Not specified"
        extra = await self._gather_context(topic, dossier_id)
        all_evidence = (evidence or []) + extra
        evidence_text = "\n".join(f"- {e}" for e in all_evidence[:8]) or "Not provided"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SCORE_PROMPT.format(
                topic=topic,
                claims_text=claims_text,
                methodology=methodology or "Not specified",
                evidence_text=evidence_text,
                domain=domain or "general research",
            ),
            system=SCORE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        quality = data.get("quality", data)

        return {
            "topic": topic,
            "overall_score": quality.get("overall_score", 0),
            "grade": quality.get("grade", "?"),
            "dimensions": quality.get("dimensions", []),
            "critical_flaws": quality.get("critical_flaws", []),
            "strengths": quality.get("strengths", []),
            "improvement_actions": quality.get("improvement_actions", []),
            "comparison_percentile": quality.get("comparison_percentile", 0),
            "publication_readiness": quality.get("publication_readiness", ""),
        }

    async def benchmark(
        self,
        research: str,
        *,
        domain: str = "",
        claims: list[str] | None = None,
    ) -> dict:
        """Benchmark research against field standards."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(f"- {c}" for c in (claims or [])[:5]) or "Not specified"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BENCHMARK_PROMPT.format(
                research=research,
                domain=domain or "general",
                claims_text=claims_text,
            ),
            system=BENCHMARK_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        bench = data.get("benchmark", data)

        return {
            "field_position": bench.get("field_position", ""),
            "compared_to": bench.get("compared_to", []),
            "field_standards": bench.get("field_standards", []),
            "what_top_papers_do_differently": bench.get("what_top_papers_do_differently", []),
            "achievable_improvements": bench.get("achievable_improvements", []),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
