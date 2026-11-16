import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

CONN = "postgresql://postgres:localdev@localhost:5433/postgres"

# (text, source, heading) — the metadata from card 02
chunks = [
    ("Cats sleep between 12 and 16 hours a day.", "cats.md", "Sleep"),
    ("Kittens need to be fed four times a day.", "cats.md", "Feeding"),
    ("Most cats groom themselves for hours at a time.", "cats.md", "Grooming"),
    ("Error 429 means you have hit the rate limit.", "api.md", "Errors"),
    ("To install the package, run pip install.", "api.md", "Setup"),
    ("Retry with exponential backoff after a 429.", "api.md", "Errors"),
]

model = SentenceTransformer("all-MiniLM-L6-v2")
vectors = model.encode([c[0] for c in chunks])

with psycopg.connect(CONN) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        for (content, source, heading), vector in zip(chunks, vectors):
            cur.execute(
                "INSERT INTO chunks (content, source, heading, embedding) "
                "VALUES (%s, %s, %s, %s)",
                (content, source, heading, vector),
            )

print(f"inserted {len(chunks)} chunks")