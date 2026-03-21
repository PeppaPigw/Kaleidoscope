"""Paper QA engine — RAG-based question answering over paper content."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.llm_client import LLMClient
from app.models.paper import Paper
from app.services.extraction.chunker import TextChunker
from app.services.extraction.prompts import (
    QA_SYSTEM,
    QA_PROMPT,
    QA_MULTI_DOC_SYSTEM,
    QA_MULTI_DOC_PROMPT,
)

logger = structlog.get_logger(__name__)


class QAResult:
    """Result of a QA query."""

    def __init__(
        self, answer: str, sources: list[dict],
        model: str = "", paper_id: str = "",
    ):
        self.answer = answer
        self.sources = sources  # [{chunk_index, section, text_snippet}]
        self.model = model
        self.paper_id = paper_id

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "model": self.model,
            "paper_id": self.paper_id,
        }


class PaperQAEngine:
    """
    Answer questions about papers using RAG.

    Flow:
    1. Chunk paper full-text into passages
    2. Embed chunks using LLM embedding API
    3. Retrieve top-k relevant chunks by cosine similarity
    4. LLM generates answer with source citations
    """

    def __init__(self, db: AsyncSession, llm: LLMClient | None = None):
        self.db = db
        self.llm = llm or LLMClient()
        self.chunker = TextChunker(max_chunk_size=400, overlap=50)

    async def ask(
        self, paper_id: str, question: str, top_k: int = 5,
    ) -> QAResult:
        """Answer a question about a single paper."""
        log = logger.bind(paper_id=paper_id, question=question[:100])

        # Load paper
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return QAResult(
                answer="Paper not found.",
                sources=[], paper_id=paper_id,
            )

        # Get full text
        fulltext = TextChunker.prepare_paper_text(paper)
        if not fulltext or fulltext == "(not available)":
            # Fallback to abstract-only QA
            if paper.abstract:
                fulltext = f"Title: {paper.title}\n\nAbstract: {paper.abstract}"
            else:
                return QAResult(
                    answer="No text content available for this paper.",
                    sources=[], paper_id=paper_id,
                )

        # Chunk the text
        chunks = self.chunker.chunk_paper(paper_id, fulltext)
        if not chunks:
            return QAResult(
                answer="Could not extract text passages from this paper.",
                sources=[], paper_id=paper_id,
            )

        # Retrieve relevant chunks
        # For simplicity in v1, use keyword matching instead of full vector retrieval
        # (vector retrieval can be added later with Qdrant chunk embeddings)
        relevant = self._keyword_retrieve(question, chunks, top_k=top_k)

        # Build context
        context = "\n\n".join(
            f"[{i+1}] (Section: {c['section'] or 'unknown'})\n{c['text']}"
            for i, c in enumerate(relevant)
        )

        prompt = QA_PROMPT.format(question=question, context=context)

        answer = await self.llm.complete(
            prompt=prompt, system=QA_SYSTEM,
            model="gpt-4o-mini", max_tokens=1000,
        )

        sources = [
            {
                "chunk_index": c["chunk_index"],
                "section": c["section"],
                "text_snippet": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"],
            }
            for c in relevant
        ]

        log.info("qa_answered", chunks_used=len(relevant))
        return QAResult(
            answer=answer, sources=sources,
            model="gpt-4o-mini", paper_id=paper_id,
        )

    async def ask_collection(
        self, paper_ids: list[str], question: str, top_k_per_paper: int = 3,
    ) -> QAResult:
        """Answer a question across multiple papers."""
        log = logger.bind(papers=len(paper_ids), question=question[:100])

        papers_context = []
        all_sources = []

        for pid in paper_ids[:10]:  # Cap at 10 papers for context limit
            result = await self.db.execute(
                select(Paper).where(Paper.id == pid)
            )
            paper = result.scalar_one_or_none()
            if not paper:
                continue

            fulltext = TextChunker.prepare_paper_text(paper)
            if not fulltext:
                continue

            chunks = self.chunker.chunk_paper(pid, fulltext)
            relevant = self._keyword_retrieve(question, chunks, top_k=top_k_per_paper)

            if relevant:
                paper_section = f"\n--- Paper: {paper.title} (DOI: {paper.doi or 'N/A'}) ---\n"
                paper_section += "\n".join(
                    f"[{c['chunk_index']+1}] {c['text'][:500]}"
                    for c in relevant
                )
                papers_context.append(paper_section)

                for c in relevant:
                    all_sources.append({
                        "paper_id": pid,
                        "paper_title": paper.title,
                        "chunk_index": c["chunk_index"],
                        "section": c["section"],
                        "text_snippet": c["text"][:200],
                    })

        if not papers_context:
            return QAResult(
                answer="No relevant content found across the specified papers.",
                sources=[], paper_id="",
            )

        prompt = QA_MULTI_DOC_PROMPT.format(
            question=question,
            papers_context="\n\n".join(papers_context),
        )

        answer = await self.llm.complete(
            prompt=prompt, system=QA_MULTI_DOC_SYSTEM,
            model="gpt-4o-mini", max_tokens=1500,
        )

        log.info("multi_doc_qa_answered", papers_used=len(papers_context),
                 sources=len(all_sources))
        return QAResult(
            answer=answer, sources=all_sources,
            model="gpt-4o-mini", paper_id="",
        )

    def _keyword_retrieve(
        self, question: str, chunks: list[dict], top_k: int = 5
    ) -> list[dict]:
        """
        Simple keyword-based retrieval (v1 fallback).

        Scores chunks by word overlap with the question.
        TODO: Replace with embedding-based retrieval using Qdrant.
        """
        question_words = set(question.lower().split())
        # Remove stopwords
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                      "at", "to", "for", "of", "with", "by", "from", "this",
                      "that", "it", "and", "or", "but", "not", "what", "how",
                      "does", "do", "did", "can", "will", "would", "should"}
        question_words -= stopwords

        scored = []
        for chunk in chunks:
            chunk_words = set(chunk["text"].lower().split())
            overlap = len(question_words & chunk_words)
            scored.append((overlap, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    async def close(self) -> None:
        await self.llm.close()
