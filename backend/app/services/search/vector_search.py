"""Vector semantic search via Qdrant."""

import time
import uuid

import structlog
from qdrant_client import QdrantClient, models

from app.config import settings

logger = structlog.get_logger(__name__)

# Collection configurations following database-guidelines.md
PAPER_COLLECTION = "paper_embeddings"
PAPER_VECTOR_DIM = 768  # SPECTER2 output dimension
CHUNK_COLLECTION = "chunk_embeddings"
CHUNK_VECTOR_DIM = 1024  # BGE-M3 output dimension


class VectorSearchService:
    """
    Semantic search via SPECTER2/BGE-M3 embeddings stored in Qdrant.

    Collections:
    - paper_embeddings: Title + abstract embeddings (SPECTER2, 768d)
    - chunk_embeddings: Full-text paragraph chunks (BGE-M3, 1024d)
    """

    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.qdrant_url)
        self._encoder = None  # Lazy-loaded
        self._collections_initialized = False

    def _ensure_collections(self) -> None:
        """Create Qdrant collections if they don't exist."""
        if self._collections_initialized:
            return

        for name, dim in [
            (PAPER_COLLECTION, PAPER_VECTOR_DIM),
            (CHUNK_COLLECTION, CHUNK_VECTOR_DIM),
        ]:
            try:
                self.client.get_collection(name)
            except Exception:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=dim,
                        distance=models.Distance.COSINE,
                    ),
                )
                logger.info("qdrant_collection_created", name=name, dim=dim)

        self._collections_initialized = True

    def _get_encoder(self):
        """Lazy-load the sentence transformer model."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("allenai/specter2_base")
                logger.info("embedding_model_loaded", model="specter2_base")
            except ImportError:
                logger.error("sentence_transformers_not_installed")
                raise RuntimeError(
                    "sentence-transformers is required for vector search. "
                    "Install with: pip install sentence-transformers"
                )
        return self._encoder

    def encode_text(self, text: str) -> list[float]:
        """Encode text into a vector embedding."""
        encoder = self._get_encoder()
        embedding = encoder.encode(text, normalize_embeddings=True)
        return embedding.tolist()

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
