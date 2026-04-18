"""Local RAG service using embeddings + LLM."""

from __future__ import annotations

from typing import Any
import time

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError

from app.clients.llm_client import LLMClient
from app.services.collection_service import CollectionService
from app.services.vector_search_service import VectorSearchService

logger = structlog.get_logger(__name__)

COLLECTION_QA_PROMPT = """You are a research assistant helping analyze academic papers. Answer the question based on the following excerpts from research papers.

Relevant excerpts:
{context}

Question: {question}

Instructions:
- Answer based on the excerpts above
- If the excerpts don't contain relevant information, say so clearly
- Cite specific papers and sections in your answer using [Paper Title, Section]
- Be concise and accurate

Answer:"""


class LocalRAGService:
    """Local RAG service using vector search + LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_search = VectorSearchService(db)
        self.collection_service = CollectionService(db)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((OperationalError, SQLAlchemyTimeoutError)),
        before_sleep=before_sleep_log(logger, "warning"),
    )
    async def ask_collection(
        self,
        collection_id: str,
        question: str,
        top_k: int = 10,
        min_similarity: float = 0.3,
    ) -> dict[str, Any]:
        """
        Answer a question based on papers in a collection.

        Pipeline:
        1. Get paper_ids from collection
        2. Embed the question
        3. Vector search for relevant chunks
        4. Build context from chunks
        5. Call LLM with context + question
        6. Return answer + sources

        Args:
            collection_id: Collection UUID
            question: User's question
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold

        Returns:
            {
                "answer": str,
                "sources": list[dict],
                "chunks_found": int,
                "latency_ms": int
            }
        """
        # Validate inputs
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "chunks_found": 0,
                "latency_ms": 0,
                "error": "empty_question",
            }

        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            return {
                "answer": "Invalid top_k parameter. Must be between 1 and 50.",
                "sources": [],
                "chunks_found": 0,
                "latency_ms": 0,
                "error": "invalid_top_k",
            }

        started = time.perf_counter()

        # 1. Get paper IDs from collection
        try:
            papers = await self.collection_service.get_collection_papers(collection_id)
            paper_ids = [str(p["paper_id"]) for p in papers]
        except Exception as exc:
            logger.error(
                "collection_fetch_failed",
                collection_id=collection_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return {
                "answer": "Failed to fetch papers from collection. Please try again.",
                "sources": [],
                "chunks_found": 0,
                "error": f"collection_fetch_error: {type(exc).__name__}",
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }

        if not paper_ids:
            return {
                "answer": "This collection has no papers yet. Add papers to start chatting.",
                "sources": [],
                "chunks_found": 0,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }

        logger.info(
            "local_rag_query_start",
            collection_id=collection_id,
            paper_count=len(paper_ids),
            question_length=len(question),
        )

        # 2. Vector search for relevant chunks
        try:
            chunks = await self.vector_search.search_by_text(
                query_text=question,
                paper_ids=paper_ids,
                top_k=top_k,
                min_similarity=min_similarity,
            )
        except ValueError as exc:
            logger.warning(
                "vector_search_validation_error",
                collection_id=collection_id,
                error=str(exc),
            )
            return {
                "answer": f"Invalid search parameters: {str(exc)}",
                "sources": [],
                "chunks_found": 0,
                "error": "validation_error",
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
        except Exception as exc:
            logger.error(
                "vector_search_failed",
                collection_id=collection_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return {
                "answer": "I encountered an error searching the papers. Please try again.",
                "sources": [],
                "chunks_found": 0,
                "error": f"vector_search_error: {type(exc).__name__}",
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }

        if not chunks:
            return {
                "answer": "I couldn't find relevant information in the papers to answer this question. The papers may not have been processed yet, or the question may be outside their scope.",
                "sources": [],
                "chunks_found": 0,
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }

        # 3. Build context from chunks
        context = self._build_context(chunks)

        # 4. Call LLM with context + question
        llm = LLMClient()
        try:
            prompt = COLLECTION_QA_PROMPT.format(context=context, question=question)
            answer = await llm.chat([{"role": "user", "content": prompt}])
        except Exception as exc:
            logger.error(
                "llm_generation_failed",
                collection_id=collection_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return {
                "answer": "I encountered an error generating the answer. Please try again.",
                "sources": self._format_sources(chunks),
                "chunks_found": len(chunks),
                "error": f"llm_error: {type(exc).__name__}",
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
        finally:
            await llm.close()

        # 5. Format response
        latency_ms = int((time.perf_counter() - started) * 1000)

        logger.info(
            "local_rag_query_complete",
            collection_id=collection_id,
            chunks_found=len(chunks),
            answer_length=len(answer),
            latency_ms=latency_ms,
        )

        return {
            "answer": answer,
            "sources": self._format_sources(chunks),
            "chunks_found": len(chunks),
            "latency_ms": latency_ms,
        }

    def _build_context(self, chunks: list[dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            paper_title = chunk.get("paper_title", "Unknown Paper")
            section_title = chunk.get("section_title", "")
            content = chunk.get("content", "")
            similarity = chunk.get("similarity", 0)

            # Truncate very long content
            if len(content) > 1000:
                content = content[:1000] + "..."

            context_parts.append(
                f"[{i}] Paper: {paper_title}\n"
                f"Section: {section_title}\n"
                f"Relevance: {similarity:.2f}\n"
                f"Content: {content}\n"
            )

        return "\n\n".join(context_parts)

    def _format_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format chunks as source citations."""
        sources = []
        for chunk in chunks:
            sources.append({
                "paper_id": chunk.get("paper_id"),
                "paper_title": chunk.get("paper_title"),
                "section_title": chunk.get("section_title"),
                "text_snippet": chunk.get("content", "")[:300],  # First 300 chars
                "similarity": chunk.get("similarity"),
                "doi": chunk.get("paper_doi"),
                "arxiv_id": chunk.get("paper_arxiv_id"),
            })
        return sources
