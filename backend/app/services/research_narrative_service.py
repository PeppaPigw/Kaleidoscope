"""ResearchNarrativeService — Publication-Ready Prose Generator.

Transforms structured research intelligence into coherent narratives:
executive summaries, literature review sections, methodology descriptions,
and findings narratives suitable for papers, reports, or presentations.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_SYSTEM = """You are an academic writing expert. Transform structured research intelligence into publication-ready prose. Write clearly, precisely, and with appropriate hedging for the confidence level of each claim.

Output JSON with: narrative.title, narrative.abstract (150-250 words), narrative.sections (list of heading/content/confidence 0-1), narrative.key_contributions (list), narrative.limitations_paragraph, narrative.future_work_paragraph, narrative.style (academic|executive|technical|popular), narrative.word_count, narrative.reading_level."""

NARRATIVE_PROMPT = """Generate a research narrative:

Topic: {topic}
Style: {style}
Target audience: {audience}

Structured intelligence:
{intelligence_text}

Key claims (with confidence):
{claims_text}

Generate publication-ready prose. Return ONLY valid JSON."""

ABSTRACT_SYSTEM = """You are an expert at writing research abstracts. Given findings and context, produce a structured abstract that is informative, precise, and compelling.

Output JSON with: abstract.background (1-2 sentences), abstract.objective (1 sentence), abstract.methods (1-2 sentences), abstract.results (2-3 sentences with key numbers), abstract.conclusions (1-2 sentences), abstract.keywords (list of 5-7), abstract.word_count."""

ABSTRACT_PROMPT = """Write a research abstract:

Topic: {topic}
Key findings:
{findings_text}

Methods used: {methods}
Main conclusion: {conclusion}

Write a structured abstract. Return ONLY valid JSON."""


class ResearchNarrativeService:
    """Generates publication-ready narratives from structured intelligence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_narrative(
        self,
        topic: str,
        intelligence: list[str],
        *,
        style: str = "academic",
        audience: str = "researchers",
        claims: list[dict] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Generate a full research narrative from structured intelligence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(topic, dossier_id)
        all_intel = intelligence + extra
        intelligence_text = "\n".join(f"- {i}" for i in all_intel[:10])

        claims_list = claims or []
        claims_text = "\n".join(
            f"- {c.get('claim', c.get('text', str(c)))} (conf: {c.get('confidence', '?')})"
            for c in claims_list[:8]
        ) or "Derive from intelligence above"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_PROMPT.format(
                topic=topic,
                style=style,
                audience=audience,
                intelligence_text=intelligence_text,
                claims_text=claims_text,
            ),
            system=NARRATIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)
        narr = data.get("narrative", data)

        return {
            "title": narr.get("title", topic),
            "abstract": narr.get("abstract", ""),
            "sections": narr.get("sections", []),
            "key_contributions": narr.get("key_contributions", []),
            "limitations": narr.get("limitations_paragraph", ""),
            "future_work": narr.get("future_work_paragraph", ""),
            "style": narr.get("style", style),
            "word_count": narr.get("word_count", 0),
            "reading_level": narr.get("reading_level", ""),
        }

    async def generate_abstract(
        self,
        topic: str,
        findings: list[str],
        *,
        methods: str = "",
        conclusion: str = "",
    ) -> dict:
        """Generate a structured research abstract."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        findings_text = "\n".join(f"- {f}" for f in findings[:8])

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABSTRACT_PROMPT.format(
                topic=topic,
                findings_text=findings_text,
                methods=methods or "Mixed methods",
                conclusion=conclusion or "Derive from findings",
            ),
            system=ABSTRACT_SYSTEM,
            max_tokens=2048,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        abstract = data.get("abstract", data)

        return {
            "background": abstract.get("background", ""),
            "objective": abstract.get("objective", ""),
            "methods": abstract.get("methods", ""),
            "results": abstract.get("results", ""),
            "conclusions": abstract.get("conclusions", ""),
            "keywords": abstract.get("keywords", []),
            "word_count": abstract.get("word_count", 0),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            return [r.get("payload", {}).get("text", "")[:150] for r in results]
        except Exception:
            return []
