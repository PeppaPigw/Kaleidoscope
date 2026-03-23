"""Writing support service — AI-assisted academic writing tools.

P2 WS-3: §22 (#189-200) from FeasibilityAnalysis.md

Provides:
- Related work section generation from selected papers
- Annotated bibliography creation
- Research gap analysis
- Rebuttal draft generation from reviewer comments
"""

import json

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper

logger = structlog.get_logger(__name__)

# ─── Prompt Templates ────────────────────────────────────────────

RELATED_WORK_PROMPT = """Generate a "{style}" style Related Work section from these papers.

{papers_section}

Write a cohesive Related Work section that:
1. Groups papers by theme/approach
2. Highlights connections and differences between works
3. Uses proper academic citations [Author, Year] or numbered references
4. Flows naturally between paragraphs
5. Is approximately 400-800 words

Output format: {format}

Return ONLY the related work text, no other commentary."""

ANNOTATED_BIB_PROMPT = """Create an annotated bibliography for these papers.

{papers_section}

For each paper provide:
1. Full citation (APA format)
2. Summary (2-3 sentences: what was studied, methods, key findings)
3. Evaluation (1-2 sentences: strengths, limitations, relevance)
4. Relevance (1 sentence: how it relates to the research topic)

Annotation depth: {depth}

Return the annotated bibliography as formatted text."""

GAP_ANALYSIS_PROMPT = """Analyze research gaps based on these papers and the following research question.

**Research question**: {research_question}

{papers_section}

Identify:
1. What has been thoroughly studied (well-covered areas)
2. What has been partially addressed (emerging areas)
3. What remains unexplored (clear gaps)
4. Methodological gaps (approaches not yet tried)
5. Data/domain gaps (datasets/domains not covered)
6. Potential research directions to fill each gap

Return JSON:
{{
    "well_covered": [{{"area": "...", "papers": ["..."], "summary": "..."}}],
    "partially_addressed": [{{"area": "...", "papers": ["..."], "what_remains": "..."}}],
    "unexplored": [{{"area": "...", "evidence": "...", "potential_direction": "..."}}],
    "methodological_gaps": ["..."],
    "data_gaps": ["..."],
    "recommended_directions": [{{"direction": "...", "rationale": "...", "difficulty": "easy/medium/hard"}}]
}}

Return ONLY the JSON, no other text."""

REBUTTAL_PROMPT = """Draft a point-by-point rebuttal response to these reviewer comments.

**Paper title**: {paper_title}
**Paper abstract**: {paper_abstract}

**Reviewer comments**:
{reviewer_comments}

For each comment/concern:
1. Thank the reviewer for the observation
2. Address the concern directly and professionally
3. If the concern is valid, describe what changes you would make
4. If the concern is a misunderstanding, clarify diplomatically
5. Reference specific parts of the paper when possible

Use a professional, respectful tone. Format as:

**Comment 1**: [restate concern briefly]
**Response**: [your response]

[Repeat for each comment]

Return ONLY the rebuttal text."""


class WritingService:
    """AI-assisted academic writing support."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm_client(self):
        """Lazy-load LLM client."""
        if self._llm_client is None:
            from app.clients.llm_client import LLMClient
            self._llm_client = LLMClient()
        return self._llm_client

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM and return response text."""
        client = await self._get_llm_client()
        return await client.complete(prompt=prompt, temperature=0.3)

    async def _load_papers(self, paper_ids: list[str]) -> list[Paper]:
        """Load papers by IDs."""
        result = await self.db.execute(
            select(Paper).where(
                Paper.id.in_(paper_ids), Paper.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    def _format_papers_for_prompt(self, papers: list[Paper]) -> str:
        """Format papers as a text block for LLM prompts."""
        sections = []
        for i, p in enumerate(papers, 1):
            block = f"**Paper {i}**: {p.title}\n"
            if p.doi:
                block += f"DOI: {p.doi}\n"
            if p.published_at:
                block += f"Year: {p.published_at.year}\n"
            if p.abstract:
                block += f"Abstract: {p.abstract[:500]}\n"
            sections.append(block)
        return "\n".join(sections)

    async def generate_related_work(
        self,
        paper_ids: list[str],
        style: str = "narrative",
        format: str = "markdown",
    ) -> dict:
        """
        Generate a Related Work section from selected papers.

        Args:
            paper_ids: Papers to include in the related work
            style: "narrative" (flowing), "thematic" (grouped by theme), "chronological"
            format: "markdown" or "latex"
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return {"error": "No papers found", "content": ""}

        papers_section = self._format_papers_for_prompt(papers)
        prompt = RELATED_WORK_PROMPT.format(
            style=style,
            papers_section=papers_section,
            format=format,
        )

        try:
            content = await self._call_llm(prompt)
            return {
                "content": content,
                "paper_count": len(papers),
                "style": style,
                "format": format,
                "citations": [
                    {"id": str(p.id), "title": p.title, "doi": p.doi}
                    for p in papers
                ],
            }
        except Exception as e:
            logger.error("related_work_failed", error=str(e))
            return {"error": str(e), "content": ""}

    async def generate_annotated_bibliography(
        self,
        paper_ids: list[str],
        annotation_depth: str = "detailed",
    ) -> dict:
        """
        Generate an annotated bibliography for selected papers.

        Args:
            paper_ids: Papers to annotate
            annotation_depth: "brief" (1-2 sentences) or "detailed" (full annotation)
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return {"error": "No papers found", "content": ""}

        papers_section = self._format_papers_for_prompt(papers)
        prompt = ANNOTATED_BIB_PROMPT.format(
            papers_section=papers_section,
            depth=annotation_depth,
        )

        try:
            content = await self._call_llm(prompt)
            return {
                "content": content,
                "paper_count": len(papers),
                "depth": annotation_depth,
            }
        except Exception as e:
            logger.error("annotated_bib_failed", error=str(e))
            return {"error": str(e), "content": ""}

    async def analyze_gaps(
        self,
        paper_ids: list[str],
        research_question: str,
    ) -> dict:
        """
        Identify research gaps from a set of papers and a research question.
        """
        papers = await self._load_papers(paper_ids)
        if not papers:
            return {"error": "No papers found"}

        papers_section = self._format_papers_for_prompt(papers)
        prompt = GAP_ANALYSIS_PROMPT.format(
            research_question=research_question,
            papers_section=papers_section,
        )

        try:
            response = await self._call_llm(prompt)
            result = json.loads(response)
            return {
                "research_question": research_question,
                "paper_count": len(papers),
                **result,
            }
        except json.JSONDecodeError:
            return {
                "research_question": research_question,
                "raw_analysis": response,
                "paper_count": len(papers),
            }
        except Exception as e:
            logger.error("gap_analysis_failed", error=str(e))
            return {"error": str(e)}

    async def draft_rebuttal(
        self,
        paper_id: str,
        reviewer_comments: str,
    ) -> dict:
        """
        Draft a point-by-point rebuttal response to reviewer comments.
        """
        result = await self.db.execute(
            select(Paper).where(
                Paper.id == paper_id, Paper.deleted_at.is_(None)
            )
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return {"error": "Paper not found"}

        prompt = REBUTTAL_PROMPT.format(
            paper_title=paper.title,
            paper_abstract=paper.abstract or "",
            reviewer_comments=reviewer_comments,
        )

        try:
            content = await self._call_llm(prompt)
            return {
                "paper_id": str(paper.id),
                "paper_title": paper.title,
                "rebuttal": content,
            }
        except Exception as e:
            logger.error("rebuttal_draft_failed", error=str(e))
            return {"error": str(e)}

    async def close(self):
        if self._llm_client:
            try:
                await self._llm_client.close()
            except Exception:
                pass
