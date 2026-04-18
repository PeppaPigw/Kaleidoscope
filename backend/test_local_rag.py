"""Test script for local RAG system."""

import asyncio
import sys
sys.path.insert(0, '/Users/pigpeppa/Downloads/Kaleidoscope/backend')

async def test_vector_search():
    from app.dependencies import async_session_factory
    from app.services.vector_search_service import VectorSearchService

    print("Testing vector search...")

    async with async_session_factory() as session:
        service = VectorSearchService(session)

        # Test with a simple query
        paper_ids = [
            "66745585-e20d-440e-9484-38a3a9a56a1c",
            "4457a5f1-f038-47ad-bb03-5b5f1a4f7357",
            "c7d081b9-b4f2-491e-a9d1-3c3c68f95102"
        ]

        try:
            results = await service.search_by_text(
                query_text="narrative visualization",
                paper_ids=paper_ids,
                top_k=3,
                min_similarity=0.0
            )

            print(f"\n✅ Vector search successful!")
            print(f"Found {len(results)} chunks")

            for i, result in enumerate(results[:2], 1):
                print(f"\n[{i}] {result['paper_title']}")
                print(f"    Section: {result['section_title']}")
                print(f"    Similarity: {result['similarity']:.3f}")
                print(f"    Content: {result['content'][:100]}...")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_search())
