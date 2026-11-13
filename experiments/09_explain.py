import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

CONN = "postgresql://postgres:localdev@localhost:5433/postgres"

model = SentenceTransformer("all-MiniLM-L6-v2")
query_vector = model.encode("how long do cats sleep")

with psycopg.connect(CONN) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            EXPLAIN ANALYZE
            SELECT content
            FROM chunks
            ORDER BY embedding <=> %s
            LIMIT 3
            """,
            (query_vector,),
        )
        for row in cur.fetchall():
            print(row[0])