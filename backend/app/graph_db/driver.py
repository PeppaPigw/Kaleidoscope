"""Neo4j async driver wrapper — connection management and query execution."""

import structlog
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import settings

logger = structlog.get_logger(__name__)

# Module-level driver singleton
_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    """Get or create the Neo4j async driver."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        # Verify connectivity
        try:
            await _driver.verify_connectivity()
            logger.info("neo4j_connected", uri=settings.neo4j_uri)
        except Exception as e:
            logger.error("neo4j_connection_failed", error=str(e))
            raise
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("neo4j_driver_closed")


async def run_query(
    query: str,
    parameters: dict | None = None,
    database: str = "neo4j",
) -> list[dict]:
    """
    Execute a Cypher query and return results as list of dicts.

    This is the primary interface for all Neo4j operations.
    """
    driver = await get_driver()
    async with driver.session(database=database) as session:
        result = await session.run(query, parameters or {})
        records = await result.data()
        return records


async def run_write(
    query: str,
    parameters: dict | None = None,
    database: str = "neo4j",
) -> dict:
    """
    Execute a write (CREATE/MERGE/DELETE) query.

    Returns summary counters.
    """
    driver = await get_driver()
    async with driver.session(database=database) as session:
        result = await session.run(query, parameters or {})
        summary = await result.consume()
        return {
            "nodes_created": summary.counters.nodes_created,
            "relationships_created": summary.counters.relationships_created,
            "properties_set": summary.counters.properties_set,
        }


async def ensure_indexes() -> None:
    """Create Neo4j indexes and constraints for the schema."""
    driver = await get_driver()
    async with driver.session() as session:
        # Unique constraint on Paper.id
        await session.run(
            "CREATE CONSTRAINT paper_id IF NOT EXISTS "
            "FOR (p:Paper) REQUIRE p.id IS UNIQUE"
        )
        # Unique constraint on Author.id
        await session.run(
            "CREATE CONSTRAINT author_id IF NOT EXISTS "
            "FOR (a:Author) REQUIRE a.id IS UNIQUE"
        )
        # Index on Paper.doi
        await session.run(
            "CREATE INDEX paper_doi IF NOT EXISTS FOR (p:Paper) ON (p.doi)"
        )
        # Index on Paper.arxiv_id
        await session.run(
            "CREATE INDEX paper_arxiv IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id)"
        )
        logger.info("neo4j_indexes_ensured")
