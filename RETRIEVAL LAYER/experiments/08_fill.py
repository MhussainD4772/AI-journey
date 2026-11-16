import numpy as np
import psycopg
from pgvector.psycopg import register_vector

CONN = "postgresql://postgres:localdev@localhost:5433/postgres"

N = 20_000

# Seeded so the numbers are the same if you rerun it.
rng = np.random.default_rng(42)
vectors = rng.normal(size=(N, 384)).astype(np.float32)

rows = [(f"filler chunk {i}", "filler", v) for i, v in enumerate(vectors)]

with psycopg.connect(CONN) as conn:
    register_vector(conn)
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO chunks (content, source, embedding) VALUES (%s, %s, %s)",
            rows,
        )

print(f"inserted {N} filler rows")