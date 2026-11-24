from dataclasses import dataclass

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

import config

RRF_K = 60

_model: SentenceTransformer | None = None


def model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(config.MODEL)
    return _model


@dataclass
class Result:
    chunk_key: str
    content: str
    paper_id: str
    title: str
    page: int
    score: float


SELECT_COLS = "chunk_key, content, paper_id, title, page"


def vector_search(
    query: str,
    limit: int = 5,
    version: str | None = None,
    paper_id: str | None = None,
) -> list[Result]:
    qv = model().encode(query)
    version = version or config.VERSION

    where = ["version = %s"]
    params: list = [qv, version]

    if paper_id:
        where.append("paper_id = %s")
        params.append(paper_id)

    params += [qv, limit]

    sql = f"""
        SELECT {SELECT_COLS}, 1 - (embedding <=> %s) AS score
        FROM chunks
        WHERE {" AND ".join(where)}
        ORDER BY embedding <=> %s
        LIMIT %s
    """

    with psycopg.connect(config.CONN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [Result(*row) for row in cur.fetchall()]


def keyword_search(
    query: str,
    limit: int = 5,
    version: str | None = None,
    paper_id: str | None = None,
) -> list[Result]:
    version = version or config.VERSION

    where = [
        "version = %s",
        "tsv @@ websearch_to_tsquery('english', %s)",
    ]
    params: list = [query, version, query]

    if paper_id:
        where.append("paper_id = %s")
        params.append(paper_id)

    params.append(limit)

    sql = f"""
        SELECT {SELECT_COLS},
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
    version: str | None = None,
    paper_id: str | None = None,
    pool: int = 20,
) -> list[Result]:
    dense = vector_search(query, pool, version, paper_id)
    sparse = keyword_search(query, pool, version, paper_id)

    scores: dict[str, float] = {}
    seen: dict[str, Result] = {}

    for results in (dense, sparse):
        for rank, r in enumerate(results, start=1):
            scores[r.chunk_key] = scores.get(r.chunk_key, 0.0) + 1.0 / (RRF_K + rank)
            seen[r.chunk_key] = r

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    return [
        Result(
            chunk_key=seen[key].chunk_key,
            content=seen[key].content,
            paper_id=seen[key].paper_id,
            title=seen[key].title,
            page=seen[key].page,
            score=score,
        )
        for key, score in ranked[:limit]
    ]