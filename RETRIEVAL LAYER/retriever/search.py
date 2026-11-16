from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from retriever import config

# Reciprocal Rank Fusion constant. 60 is the value from the original paper.
RRF_K = 60

_model: SentenceTransformer | None = None


def model() -> SentenceTransformer:
    """Load the embedding model once, on first use."""
    global _model
    if _model is None:
        _model = SentenceTransformer(config.MODEL)
    return _model


@dataclass
class Result:
    id: int
    content: str
    source: str
    heading: str
    score: float


def vector_search(query: str, limit: int = 5, source: str | None = None) -> list[Result]:
    """Rank chunks by meaning. Always returns `limit` rows if the table has them."""
    qv = model().encode(query)

    where = ""
    params: list = [qv]

    if source:
        where = "WHERE source LIKE %s"
        params.append(f"%{source}%")

    params += [qv, limit]

    sql = f"""
        SELECT id,
               content,
               source,
               heading,
               1 - (embedding <=> %s) AS score
        FROM chunks
        {where}
        ORDER BY embedding <=> %s
        LIMIT %s
    """

    with psycopg.connect(config.CONN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [Result(*row) for row in cur.fetchall()]


def keyword_search(query: str, limit: int = 5, source: str | None = None) -> list[Result]:
    """Rank chunks by exact word matches. Returns nothing if no chunk has them all."""
    where = ["tsv @@ websearch_to_tsquery('english', %s)"]
    params: list = [query, query]        # one for the score, one for the filter

    if source:
        where.append("source LIKE %s")
        params.append(f"%{source}%")

    params.append(limit)

    sql = f"""
        SELECT id,
               content,
               source,
               heading,
               ts_rank(tsv, websearch_to_tsquery('english', %s)) AS score
        FROM chunks
        WHERE {" AND ".join(where)}
        ORDER BY score DESC
        LIMIT %s
    """

    with psycopg.connect(config.CONN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [Result(*row) for row in cur.fetchall()]


def hybrid_search(
    query: str,
    limit: int = 5,
    source: str | None = None,
    pool: int = 20,
) -> list[Result]:
    """Merge both rankings by position using Reciprocal Rank Fusion."""
    dense = vector_search(query, limit=pool, source=source)
    sparse = keyword_search(query, limit=pool, source=source)

    scores: dict[int, float] = {}
    seen: dict[int, Result] = {}

    for results in (dense, sparse):
        for rank, r in enumerate(results, start=1):
            scores[r.id] = scores.get(r.id, 0.0) + 1.0 / (RRF_K + rank)
            seen[r.id] = r

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    return [
        Result(
            id=seen[cid].id,
            content=seen[cid].content,
            source=seen[cid].source,
            heading=seen[cid].heading,
            score=score,
        )
        for cid, score in ranked[:limit]
    ]