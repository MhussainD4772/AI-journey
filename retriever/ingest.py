import sys
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

from retriever import config
from retriever.chunk import Chunk, chunk_file


def collect(root: Path) -> list[Chunk]:
    """Every markdown file under root, chunked, minus the skip list."""
    chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        if path.name in config.SKIP_FILES:
            continue
        chunks.extend(chunk_file(path, root))
    return chunks


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m retriever.ingest <docs-root>")
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"not a directory: {root}")
        sys.exit(1)

    chunks = collect(root)
    print(f"{len(chunks)} chunks from {root}")

    model = SentenceTransformer(config.MODEL)
    vectors = model.encode(
        [c.text for c in chunks],
        batch_size=config.BATCH_SIZE,
        show_progress_bar=True,
    )

    rows = [
        (c.text, c.source, c.heading, v)
        for c, v in zip(chunks, vectors)
    ]

    with psycopg.connect(config.CONN) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE chunks RESTART IDENTITY")
            cur.executemany(
                "INSERT INTO chunks (content, source, heading, embedding) "
                "VALUES (%s, %s, %s, %s)",
                rows,
            )

    print(f"stored {len(rows)} chunks")


if __name__ == "__main__":
    main()