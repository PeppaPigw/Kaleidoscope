"""Cypher query templates for citation graph operations."""

# ─── Paper Node ──────────────────────────────────────────────────

UPSERT_PAPER = """
MERGE (p:Paper {id: $id})
SET p.doi = $doi,
    p.arxiv_id = $arxiv_id,
    p.title = $title,
    p.year = $year,
    p.citation_count = $citation_count,
    p.paper_type = $paper_type,
    p.updated_at = datetime()
RETURN p
"""

# ─── Citation Edges ──────────────────────────────────────────────

UPSERT_CITATION = """
MATCH (citing:Paper {id: $citing_id})
MERGE (cited:Paper {id: $cited_id})
ON CREATE SET cited.doi = $cited_doi,
              cited.title = $cited_title,
              cited.year = $cited_year,
              cited.is_stub = true
MERGE (citing)-[r:CITES]->(cited)
SET r.context = $context,
    r.position = $position
RETURN citing.id, cited.id
"""

# ─── Forward citations (papers that cite this paper) ─────────────

GET_FORWARD_CITATIONS = """
MATCH (p:Paper {id: $paper_id})<-[:CITES]-(citing:Paper)
RETURN citing.id AS id, citing.doi AS doi, citing.title AS title,
       citing.year AS year, citing.citation_count AS citation_count,
       citing.is_stub AS is_stub
ORDER BY citing.year DESC
LIMIT $limit
"""

# ─── Backward citations (references this paper cites) ────────────

GET_BACKWARD_CITATIONS = """
MATCH (p:Paper {id: $paper_id})-[:CITES]->(cited:Paper)
RETURN cited.id AS id, cited.doi AS doi, cited.title AS title,
       cited.year AS year, cited.citation_count AS citation_count,
       cited.is_stub AS is_stub
ORDER BY cited.year DESC
LIMIT $limit
"""

# ─── Co-citation analysis ────────────────────────────────────────
# Papers frequently cited alongside the target paper

CO_CITATION_ANALYSIS = """
MATCH (p:Paper {id: $paper_id})<-[:CITES]-(citing:Paper)-[:CITES]->(co_cited:Paper)
WHERE co_cited.id <> $paper_id
WITH co_cited, count(citing) AS co_citation_count
ORDER BY co_citation_count DESC
LIMIT $limit
RETURN co_cited.id AS id, co_cited.doi AS doi, co_cited.title AS title,
       co_cited.year AS year, co_citation_count
"""

# ─── Bibliographic coupling ──────────────────────────────────────
# Papers that cite the same references as the target

BIBLIOGRAPHIC_COUPLING = """
MATCH (p:Paper {id: $paper_id})-[:CITES]->(ref:Paper)<-[:CITES]-(coupled:Paper)
WHERE coupled.id <> $paper_id
WITH coupled, count(ref) AS shared_references
ORDER BY shared_references DESC
LIMIT $limit
RETURN coupled.id AS id, coupled.doi AS doi, coupled.title AS title,
       coupled.year AS year, shared_references
"""

# ─── Graph neighborhood (for visualization) ──────────────────────

GRAPH_NEIGHBORHOOD = """
MATCH (center:Paper {id: $paper_id})
OPTIONAL MATCH (center)-[r1:CITES]->(cited:Paper)
OPTIONAL MATCH (center)<-[r2:CITES]-(citing:Paper)
WITH center, collect(DISTINCT {id: cited.id, doi: cited.doi, title: cited.title,
     year: cited.year, type: 'cited'}) AS cited_nodes,
     collect(DISTINCT {id: citing.id, doi: citing.doi, title: citing.title,
     year: citing.year, type: 'citing'}) AS citing_nodes
RETURN center.id AS center_id, cited_nodes, citing_nodes
"""

# ─── Graph neighborhood multi-hop ────────────────────────────────

GRAPH_NEIGHBORHOOD_2HOP = """
MATCH path = (center:Paper {id: $paper_id})-[:CITES*1..2]-(neighbor:Paper)
WITH DISTINCT neighbor, length(path) AS distance
RETURN neighbor.id AS id, neighbor.doi AS doi, neighbor.title AS title,
       neighbor.year AS year, distance
ORDER BY distance, neighbor.year DESC
LIMIT $limit
"""

# ─── Author node ─────────────────────────────────────────────────

UPSERT_AUTHOR = """
MERGE (a:Author {id: $id})
SET a.name = $name,
    a.orcid = $orcid
RETURN a
"""

LINK_AUTHOR_PAPER = """
MATCH (a:Author {id: $author_id}), (p:Paper {id: $paper_id})
MERGE (a)-[r:AUTHORED]->(p)
SET r.position = $position
RETURN a.id, p.id
"""

# ─── Stats ───────────────────────────────────────────────────────

GRAPH_STATS = """
MATCH (p:Paper) WITH count(p) AS paper_count
MATCH ()-[r:CITES]->() WITH paper_count, count(r) AS citation_count
MATCH (a:Author) WITH paper_count, citation_count, count(a) AS author_count
RETURN paper_count, citation_count, author_count
"""
