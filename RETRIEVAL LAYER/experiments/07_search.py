import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

CONN = "postgresql://postgres:localdev@localhost:5433/postgres"

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "how long do cats sleep"
query_vector = model.encode(query)

with psycopg.connect(CONN) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content,
                   source,
                   heading,
                   1 - (embedding <=> %s) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s
            LIMIT 3
            """,
            (query_vector, query_vector),
        )

        print(f'query: "{query}"\n')
        for content, source, heading, similarity in cur.fetchall():
            print(f"{similarity:.3f}  [{source} > {heading}]  {content}")