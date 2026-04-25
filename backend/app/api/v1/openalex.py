from __future__ import annotations

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/openalex", tags=["openalex"])

_SELECT_FIELDS = (
    "id,display_name,doi,publication_year,publication_date,"
    "abstract_inverted_index,referenced_works,related_works,"
    "authorships,topics,keywords,concepts,cited_by_count,"
    "primary_location,primary_topic,open_access,fwci,language"
)


def _api_url(path: str = "") -> str:
    return settings.openalex_api_url.rstrip("/") + path


def _user_agent() -> str:
    email = settings.openalex_email
    contact = f" (mailto:{email})" if email else ""
    return f"Kaleidoscope/1.0{contact}"


def _openalex_dependency_error(exc: httpx.HTTPError) -> HTTPException:
    return HTTPException(
        status_code=424,
        detail={
            "code": "OPENALEX_REQUEST_FAILED",
            "message": "OpenAlex request failed.",
            "upstream_error": str(exc)[:240],
        },
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _reconstruct_abstract(inv_idx: dict | None) -> str:
    if not inv_idx:
        return ""
    try:
        max_pos = max(pos for positions in inv_idx.values() for pos in positions)
        words = [""] * (max_pos + 1)
        for word, positions in inv_idx.items():
            for p in positions:
                words[p] = word
        text = " ".join(w for w in words if w)
        for old, new in [
            (" ,", ","),
            (" .", "."),
            (" :", ":"),
            (" ;", ";"),
            (" )", ")"),
            ("( ", "("),
        ]:
            text = text.replace(old, new)
        return text
    except Exception:
        return ""


def _jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _similarity(focal: dict, candidate: dict) -> float:
    """Weighted Jaccard similarity: topics×0.2, keywords×0.3, concepts×0.5."""
    focal_topics = {t["id"] for t in (focal.get("topics") or []) if t.get("id")}
    cand_topics = {t["id"] for t in (candidate.get("topics") or []) if t.get("id")}

    focal_kw = {
        k["display_name"].lower()
        for k in (focal.get("keywords") or [])
        if k.get("display_name")
    }
    cand_kw = {
        k["display_name"].lower()
        for k in (candidate.get("keywords") or [])
        if k.get("display_name")
    }

    focal_concepts = {c["id"] for c in (focal.get("concepts") or []) if c.get("id")}
    cand_concepts = {c["id"] for c in (candidate.get("concepts") or []) if c.get("id")}

    return round(
        0.2 * _jaccard(focal_topics, cand_topics)
        + 0.3 * _jaccard(focal_kw, cand_kw)
        + 0.5 * _jaccard(focal_concepts, cand_concepts),
        4,
    )


def _extract_paper(work: dict) -> dict:
    authorships_full = []
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        name = author.get("display_name")
        if not name:
            continue
        raw_aid = author.get("id") or ""
        inst_names = [
            inst.get("display_name")
            for inst in (a.get("institutions") or [])[:3]
            if inst.get("display_name")
        ]
        authorships_full.append(
            {
                "name": name,
                "openalex_id": raw_aid.replace("https://openalex.org/", ""),
                "orcid": author.get("orcid"),
                "position": a.get("author_position"),
                "institutions": inst_names,
            }
        )

    primary_loc = work.get("primary_location") or {}
    source = primary_loc.get("source") or {}
    venue = source.get("display_name")
    oa = work.get("open_access") or {}
    oa_url = oa.get("oa_url") or primary_loc.get("landing_page_url")
    raw_id: str = work.get("id", "")
    openalex_id = raw_id.replace("https://openalex.org/", "")
    primary_topic_obj = work.get("primary_topic") or {}

    return {
        "openalex_id": openalex_id,
        "openalex_url": raw_id,
        "title": work.get("display_name", ""),
        "year": work.get("publication_year"),
        "authors": [a["name"] for a in authorships_full],
        "authorships": authorships_full,
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "cited_by_count": work.get("cited_by_count", 0),
        "primary_topic": primary_topic_obj.get("display_name"),
        # Keep for similarity / edge computation (stripped before client response)
        "topics": work.get("topics") or [],
        "keywords": work.get("keywords") or [],
        "concepts": work.get("concepts") or [],
        "_referenced_works": work.get("referenced_works") or [],
        "venue": venue,
        "oa_url": oa_url,
        "doi": work.get("doi"),
        "fwci": work.get("fwci"),
        "language": work.get("language"),
        "similarity_score": 0.0,
    }


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/search")
async def openalex_search(
    q: str = Query(..., min_length=1, max_length=500, description="Free-text query"),
    limit: int = Query(20, ge=5, le=50, description="Max papers to return (5-50)"),
    focal_id: str | None = Query(
        None,
        description="OpenAlex ID of the focal paper for similarity ranking. "
        "Defaults to the top relevance result.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Search OpenAlex, rank results by similarity to the focal paper, and
    return the citation-edge graph between the top results.
    """
    # Fetch up to 2× limit so trimming to top-N by similarity is meaningful
    fetch_n = min(limit * 2, settings.openalex_search_max * 2)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                _api_url("/works"),
                params={
                    "search": q,
                    "per-page": fetch_n,
                    "select": _SELECT_FIELDS,
                    "sort": "relevance_score:desc",
                },
                headers={"User-Agent": _user_agent()},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("openalex_search_failed", error=str(exc)[:240])
            raise _openalex_dependency_error(exc) from exc

    raw_results = resp.json().get("results", [])
    papers = [_extract_paper(w) for w in raw_results if w.get("id")]

    if not papers:
        return {"query": q, "focal_id": None, "total": 0, "papers": [], "edges": []}

    # Determine focal paper
    focal = next((p for p in papers if p["openalex_id"] == focal_id), None)
    if focal is None:
        focal = papers[0]

    # Score all papers (focal gets 1.0)
    for p in papers:
        p["similarity_score"] = (
            1.0 if p["openalex_id"] == focal["openalex_id"] else _similarity(focal, p)
        )

    # Sort by similarity, keep top limit
    papers.sort(key=lambda p: p["similarity_score"], reverse=True)
    papers = papers[:limit]

    # Build citation edges within the returned set
    paper_ids = {p["openalex_id"] for p in papers}
    edges: list[dict] = []
    for p in papers:
        for ref_url in p.get("_referenced_works", []):
            ref_id = ref_url.replace("https://openalex.org/", "")
            if ref_id in paper_ids and ref_id != p["openalex_id"]:
                edges.append({"source": p["openalex_id"], "target": ref_id})

    # Strip internal fields before serialising
    for p in papers:
        p.pop("_referenced_works", None)
        # Keep topics/keywords/concepts so client can re-rank when focal changes
        # (they are small arrays; bandwidth is acceptable)

    payload = {
        "query": q,
        "focal_id": focal["openalex_id"],
        "total": len(papers),
        "papers": papers,
        "edges": edges,
    }

    # Persist asynchronously (best-effort)
    try:
        from app.models.openalex_search import OpenAlexSearch

        record = OpenAlexSearch(
            query=q,
            focal_openalex_id=focal["openalex_id"],
            result_count=len(papers),
            results=payload,
        )
        db.add(record)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.warning("openalex_persist_error", error=str(exc)[:120])

    return payload


# ── Graph endpoint ────────────────────────────────────────────────────────────


class GraphRequest(BaseModel):
    paper_ids: list[str]  # Short OpenAlex IDs, e.g. ["W1632114991", "W2741809807"]


@router.post("/graph")
async def build_citation_graph(body: GraphRequest, db: AsyncSession = Depends(get_db)):
    """
    Given a list of selected OpenAlex paper IDs, fetch their full citation network:
      - The selected papers themselves (tagged is_origin=True)
      - All papers they reference (tagged is_origin=False)
    Returns the graph nodes and directed citation edges.

    Uses a single batch API call per tier (pipe-separated IDs) to minimise
    round-trips, as documented by the user's earlier notes.
    """
    if not body.paper_ids:
        raise HTTPException(status_code=400, detail="paper_ids cannot be empty")
    if len(body.paper_ids) > 20:
        raise HTTPException(status_code=400, detail="At most 20 paper_ids allowed")

    # Normalise: strip prefix if caller passed full URLs
    paper_ids = [
        pid.strip().replace("https://openalex.org/", "")
        for pid in body.paper_ids
        if pid.strip()
    ]

    # ── Step 1: Fetch origin papers ───────────────────────────────────────────
    filter_origin = "|".join(paper_ids)
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                _api_url("/works"),
                params={
                    "filter": f"openalex_id:{filter_origin}",
                    "per-page": 50,
                    "select": _SELECT_FIELDS,
                },
                headers={"User-Agent": _user_agent()},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("openalex_graph_origin_failed", error=str(exc)[:240])
            raise _openalex_dependency_error(exc) from exc

    origin_works = resp.json().get("results", [])
    # raw_id → raw work dict (needed to iterate referenced_works for edge building)
    origin_raw: dict[str, dict] = {}
    for w in origin_works:
        raw_id = w.get("id", "").replace("https://openalex.org/", "")
        origin_raw[raw_id] = w

    origin_ids = set(origin_raw.keys())

    # ── Step 2: Collect all referenced work IDs ───────────────────────────────
    ref_id_set: set[str] = set()
    for w in origin_works:
        for ref_url in (w.get("referenced_works") or [])[
            : settings.openalex_refs_per_paper
        ]:
            ref_id = ref_url.replace("https://openalex.org/", "")
            if ref_id not in origin_ids:
                ref_id_set.add(ref_id)
        for rel_url in (w.get("related_works") or [])[
            : settings.openalex_related_per_paper
        ]:
            rel_id = rel_url.replace("https://openalex.org/", "")
            if rel_id not in origin_ids:
                ref_id_set.add(rel_id)

    # ── Step 3: Batch fetch referenced papers (≤ 50 at a time) ───────────────
    ref_papers: dict[str, dict] = {}
    ref_raw: dict[str, dict] = {}  # for intra-ref edge building
    ref_ids_list = list(ref_id_set)[:50]
    if ref_ids_list:
        filter_refs = "|".join(ref_ids_list)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp2 = await client.get(
                    _api_url("/works"),
                    params={
                        "filter": f"openalex_id:{filter_refs}",
                        "per-page": 50,
                        "select": _SELECT_FIELDS,
                    },
                    headers={"User-Agent": _user_agent()},
                )
                resp2.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("openalex_graph_refs_failed", error=str(exc)[:240])
                resp2 = None
            if resp2 is not None:
                for w in resp2.json().get("results", []):
                    p = _extract_paper(w)
                    ref_papers[p["openalex_id"]] = p
                    ref_raw[p["openalex_id"]] = w

    # ── Step 4: Build node list ───────────────────────────────────────────────
    all_node_ids = origin_ids | set(ref_papers.keys())
    nodes: list[dict] = []

    for oid, w in origin_raw.items():
        p = _extract_paper(w)
        p["is_origin"] = True
        p.pop("_referenced_works", None)
        nodes.append(p)

    for rid, p in ref_papers.items():
        p_clean = {k: v for k, v in p.items() if k != "_referenced_works"}
        p_clean["is_origin"] = False
        nodes.append(p_clean)

    # ── Step 5: Build directed edge list ─────────────────────────────────────
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def _add_edge(src: str, tgt: str) -> None:
        if (
            src != tgt
            and (src, tgt) not in seen
            and src in all_node_ids
            and tgt in all_node_ids
        ):
            edges.append({"source": src, "target": tgt})
            seen.add((src, tgt))

    # Origin → their references
    for oid, w in origin_raw.items():
        for ref_url in w.get("referenced_works") or []:
            _add_edge(oid, ref_url.replace("https://openalex.org/", ""))

    # Intra-reference edges (ref paper → another ref or origin paper)
    for rid, w in ref_raw.items():
        for ref_url in w.get("referenced_works") or []:
            _add_edge(rid, ref_url.replace("https://openalex.org/", ""))

    # ── Step 6: Filter out isolated nodes ────────────────────────────────────
    # Remove nodes that have no edges (neither as source nor target)
    connected_node_ids = set()
    for edge in edges:
        connected_node_ids.add(edge["source"])
        connected_node_ids.add(edge["target"])

    filtered_nodes = [n for n in nodes if n["openalex_id"] in connected_node_ids]
    isolated_count = len(nodes) - len(filtered_nodes)

    if isolated_count > 0:
        logger.info(
            "filtered_isolated_nodes",
            total_nodes=len(nodes),
            connected_nodes=len(filtered_nodes),
            isolated_count=isolated_count,
        )

    return {
        "nodes": filtered_nodes,
        "edges": edges,
        "origin_count": len([n for n in filtered_nodes if n.get("is_origin")]),
        "ref_count": len([n for n in filtered_nodes if not n.get("is_origin")]),
        "isolated_count": isolated_count,
    }
