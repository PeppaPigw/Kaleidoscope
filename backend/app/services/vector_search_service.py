"""Vector similarity search using PostgreSQL pgvector."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.paper_qa import PaperChunk

logger = structlog.get_logger(__name__)


class VectorSearchService:
    """Service for vector similarity search using pgvector."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        paper_ids: list[str] | None = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query vector (1024 dimensions)
            paper_ids: Optional list of paper IDs to filter by
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of dicts with chunk and paper metadata
        """
        # Validate inputs
        if not query_embedding or len(query_embedding) != 1024:
            raise ValueError("query_embedding must be a list of 1024 floats")

        if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
            raise ValueError("top_k must be an integer between 1 and 100")

        if (
            not isinstance(min_similarity, (int, float))
            or min_similarity < 0
            or min_similarity > 1
        ):
            raise ValueError("min_similarity must be a number between 0 and 1")

        # Calculate cosine similarity: 1 - (cosine_distance / 2)
        # pgvector's cosine_distance operator (<=>) returns values in [0, 2]
        # We convert to similarity in [0, 1] where 1 is most similar
        similarity = (1 - PaperChunk.embedding.cosine_distance(query_embedding)) / 2

        # Build query
        query = (
            select(
                PaperChunk.id.label("chunk_id"),
                PaperChunk.paper_id,
                PaperChunk.section_title,
                PaperChunk.content,
                similarity.label("similarity"),
                Paper.title.label("paper_title"),
                Paper.doi.label("paper_doi"),
                Paper.arxiv_id.label("paper_arxiv_id"),
            )
            .join(Paper, Paper.id == PaperChunk.paper_id)
            .where(PaperChunk.embedding.isnot(None))
        )

        # Filter by paper IDs if provided
        if paper_ids:
            if not paper_ids:  # Empty list
                return []
            query = query.where(PaperChunk.paper_id.in_(paper_ids))

        # Order by similarity (closest first) and limit
        query = query.order_by(
            PaperChunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        try:
            result = await self.db.execute(query)
            rows = result.fetchall()
        except Exception as exc:
            logger.error(
                "vector_search_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                paper_filter=len(paper_ids) if paper_ids else None,
                top_k=top_k,
            )
            raise

        # Filter by minimum similarity and format results
        results = []
        for row in rows:
            similarity_score = float(row.similarity)
            if similarity_score >= min_similarity:
                results.append(
                    {
                        "chunk_id": str(row.chunk_id),
                        "paper_id": str(row.paper_id),
                        "section_title": row.section_title,
                        "content": row.content,
                        "similarity": similarity_score,
                        "paper_title": row.paper_title,
                        "paper_doi": row.paper_doi,
                        "paper_arxiv_id": row.paper_arxiv_id,
                    }
                )

        logger.info(
            "vector_search_complete",
            query_dim=len(query_embedding),
            paper_filter=len(paper_ids) if paper_ids else None,
            top_k=top_k,
            results_found=len(results),
        )

        return results

    async def search_by_text(
        self,
        query_text: str,
        paper_ids: list[str] | None = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar chunks by embedding the query text first.

        Args:
            query_text: Text query to search for
            paper_ids: Optional list of paper IDs to filter by
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            Same format as search_similar_chunks
        """
        if not query_text or not query_text.strip():
            raise ValueError("query_text cannot be empty")

        from app.clients.llm_client import LLMClient

        # Embed the query text
        llm = LLMClient()
        try:
            embeddings = await llm.embed([query_text])
            query_embedding = embeddings[0]
        finally:
            await llm.close()

        # Search using the embedding
        return await self.search_similar_chunks(
            query_embedding=query_embedding,
            paper_ids=paper_ids,
            top_k=top_k,
            min_similarity=min_similarity,
        )
