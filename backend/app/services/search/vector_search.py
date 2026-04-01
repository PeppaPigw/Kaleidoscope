"""Vector semantic search via Qdrant.

Embeddings: Doubao-Embedding-Large-Text via BLSC API (default).
Fallback:   local allenai/specter2_base (set USE_LOCAL_EMBEDDER=true in .env).
"""

import asyncio
import time
import uuid

import structlog
from qdrant_client import QdrantClient, models

from app.config import settings

logger = structlog.get_logger(__name__)

# Collection configurations following database-guidelines.md
PAPER_COLLECTION = "paper_embeddings"
# Doubao-Embedding-Large-Text produces 2048-d vectors.
# The actual dim is confirmed on first embed call; Qdrant collection is created lazily.
PAPER_VECTOR_DIM = 2048
CHUNK_COLLECTION = "chunk_embeddings"
CHUNK_VECTOR_DIM = 2048  # same model for chunks


class VectorSearchService:
    """
    Semantic search via SPECTER2/BGE-M3 embeddings stored in Qdrant.

    Collections:
    - paper_embeddings: Title + abstract embeddings (SPECTER2, 768d)
    - chunk_embeddings: Full-text paragraph chunks (BGE-M3, 1024d)
    """

    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self._encoder = None          # lazy local model (fallback only)
        self._llm: "LLMClient | None" = None     # API embedder
        self._use_local = False       # set USE_LOCAL_EMBEDDER=true to prefer local
        self._collections_initialized = False
        # Check env flag
        import os
        self._use_local = os.getenv("USE_LOCAL_EMBEDDER", "").lower() in ("1", "true", "yes")

    def _get_llm(self):
        """Lazy-init the LLMClient used for API embeddings."""
        if self._llm is None:
            from app.clients.llm_client import LLMClient
            self._llm = LLMClient()
        return self._llm

    def _get_encoder(self):
        """Lazy-load local sentence-transformer (fallback only)."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("allenai/specter2_base")
                logger.info("embedding_model_loaded", model="specter2_base")
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers is required for local embedding. "
                    "Install with: pip install sentence-transformers, "
                    "or set USE_LOCAL_EMBEDDER=false to use the API."
                )
        return self._encoder

    async def encode_text_async(self, text: str) -> list[float]:
        """Encode one text string via the Doubao embedding API (async)."""
        llm = self._get_llm()
        results = await llm.embed([text], model=settings.embed_model)
        return results[0]

    def encode_text(self, text: str) -> list[float]:
        """
        Synchronous embedding (used by non-async callers such as index_paper).

        Runs the async API call in the current event loop if one is running,
        otherwise creates a new one.  Falls back to the local SPECTER2 model
        when USE_LOCAL_EMBEDDER=true.
        """
        if self._use_local:
            encoder = self._get_encoder()
            embedding = encoder.encode(text, normalize_embeddings=True)
            return embedding.tolist()

        # API path — run async embed synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Inside an async context (e.g. Celery with asyncio loop)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, self.encode_text_async(text))
                    return future.result()
            else:
                return loop.run_until_complete(self.encode_text_async(text))
        except Exception as e:
            logger.warning("api_embed_failed_fallback_local", error=str(e))
            # Last resort: local model
            encoder = self._get_encoder()
            embedding = encoder.encode(text, normalize_embeddings=True)
            return embedding.tolist()


    def _ensure_collections(self, dim: int | None = None) -> None:
        """Create Qdrant collections if they don't exist."""
        if self._collections_initialized:
            return

        effective_dim = dim or PAPER_VECTOR_DIM
        for name, d in [
            (PAPER_COLLECTION, effective_dim),
            (CHUNK_COLLECTION, effective_dim),
        ]:
            try:
                self.client.get_collection(name)
            except Exception:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=d,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info("qdrant_collection_created", name=name, dim=d)

        self._collections_initialized = True

    def search(
        self,
        query: str,
        top_k: int = 20,
        collection: str = PAPER_COLLECTION,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Search for similar papers using vector similarity.

        Returns list of {paper_id, score, payload}.
        """
        self._ensure_collections()
        start = time.monotonic()

        query_vector = self.encode_text(query)

        # Build Qdrant filter
        qdrant_filter = None
        if filters:
            conditions = []
            if filters.get("year_from"):
                conditions.append(
                    models.FieldCondition(
                        key="year",
                        range=models.Range(gte=filters["year_from"]),
                    )
                )
            if filters.get("year_to"):
                conditions.append(
                    models.FieldCondition(
                        key="year",
                        range=models.Range(lte=filters["year_to"]),
                    )
                )
            if filters.get("venue"):
                conditions.append(
                    models.FieldCondition(
                        key="venue",
                        match=models.MatchValue(value=filters["venue"]),
                    )
                )
            if filters.get("paper_type"):
                conditions.append(
                    models.FieldCondition(
                        key="paper_type",
                        match=models.MatchValue(value=filters["paper_type"]),
                    )
                )
            if filters.get("oa_status"):
                conditions.append(
                    models.FieldCondition(
                        key="oa_status",
                        match=models.MatchValue(value=filters["oa_status"]),
                    )
                )
            if filters.get("has_full_text") is not None:
                conditions.append(
                    models.FieldCondition(
                        key="has_full_text",
                        match=models.MatchValue(value=filters["has_full_text"]),
                    )
                )
            if conditions:
                qdrant_filter = models.Filter(must=conditions)

        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
        )

        elapsed = (time.monotonic() - start) * 1000
        logger.debug(
            "vector_search_complete",
            query=query[:50],
            results=len(results),
            time_ms=f"{elapsed:.1f}",
        )

        return [
            {
                "paper_id": hit.payload.get("paper_id") if hit.payload else None,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def index_paper(
        self,
        paper_id: str,
        title: str,
        abstract: str | None = None,
        year: int | None = None,
        extra_payload: dict | None = None,
    ) -> None:
        """Index a paper's embedding in Qdrant."""
        self._ensure_collections()

        text = title
        if abstract:
            text += " " + abstract

        vector = self.encode_text(text)

        payload = {
            "paper_id": paper_id,
            "title": title,
            "year": year,
        }
        if extra_payload:
            payload.update(extra_payload)

        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, paper_id))

        self.client.upsert(
            collection_name=PAPER_COLLECTION,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        logger.debug("qdrant_paper_indexed", paper_id=paper_id)

    def index_papers_batch(self, papers: list[dict]) -> None:
        """
        Batch index papers.

        Each dict should have: paper_id, title, abstract (optional), year (optional).
        """
        if not papers:
            return

        self._ensure_collections()
        points = []
        for paper in papers:
            text = paper["title"]
            if paper.get("abstract"):
                text += " " + paper["abstract"]

            vector = self.encode_text(text)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, paper["paper_id"]))

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "paper_id": paper["paper_id"],
                        "title": paper["title"],
                        "year": paper.get("year"),
                    },
                )
            )

        self.client.upsert(
            collection_name=PAPER_COLLECTION,
            points=points,
        )
        logger.info("qdrant_batch_indexed", count=len(points))

    def health_check(self) -> None:
        """Perform a lightweight Qdrant connectivity check."""
        self.client.get_collections()
