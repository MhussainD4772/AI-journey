import json
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

import config
from chunker import chunk_pages
from parse import extract_pages

HERE = Path(__file__).parent


def load_metadata() -> dict[str, dict]:
    """arXiv metadata, keyed by paper id."""
    raw = json.loads((HERE / "metadata.json").read_text())
    return {paper["id"]: paper for paper in raw}


def build_rows() -> list[dict]:
    meta = load_metadata()
    rows = []

    for pdf in sorted((HERE / "papers").glob("*.pdf")):
        paper_id = pdf.stem
        paper = meta.get(paper_id)

        if paper is None:
            print(f"no metadata for {paper_id}, skipping")
            continue

        chunks = chunk_pages(extract_pages(pdf))
        print(f"{paper_id:<16} {len(chunks):>3} chunks")

        for chunk in chunks:
            rows.append({
                "chunk_key": f"{paper_id}#{chunk.index}",
                "version": config.VERSION,
                "content": chunk.text,
                "paper_id": paper_id,
                "title": paper["title"],
                "authors": paper["authors"],
                "published": paper["published"][:10],      # ISO date, drop the time
                "categories": paper["categories"],
                "page": chunk.page,
                "chunk_index": chunk.index,
            })

    return rows


def main() -> None:
    rows = build_rows()
    print(f"\n{len(rows)} chunks, embedding...")

    model = SentenceTransformer(config.MODEL)
    vectors = model.encode(
        [r["content"] for r in rows],
        batch_size=config.BATCH_SIZE,
        show_progress_bar=True,
    )

    with psycopg.connect(config.CONN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO chunks
                    (chunk_key, version, content, embedding, paper_id,
                     title, authors, published, categories, page, chunk_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_key, version) DO NOTHING
                """,
                [
                    (r["chunk_key"], r["version"], r["content"], v, r["paper_id"],
                     r["title"], r["authors"], r["published"], r["categories"],
                     r["page"], r["chunk_index"])
                    for r, v in zip(rows, vectors)
                ],
            )
            inserted = cur.rowcount

    print(f"\ninserted {inserted} rows as version {config.VERSION}")


if __name__ == "__main__":
    main()