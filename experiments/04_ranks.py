from sentence_transformers import SentenceTransformer
import numpy as np


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


model = SentenceTransformer("all-MiniLM-L6-v2")

chunks = [
    "Cats sleep between 12 and 16 hours a day.",
    "To install the package, run pip install.",
    "Kittens need to be fed four times a day.",
    "The mortgage rate dropped half a point this quarter.",
    "Most cats groom themselves for hours at a time.",
    "Error 429 means you have hit the rate limit.",
]

query = "how long do cats sleep"

chunk_vectors = model.encode(chunks)
query_vector = model.encode(query)

# Score every chunk against the query, keep the text alongside the score.
scored = [(cosine(query_vector, v), c) for v, c in zip(chunk_vectors, chunks)]

# Sort highest first. reverse=True because sort goes low-to-high by default.
scored.sort(reverse=True)

print(f'query: "{query}"\n')
for score, chunk in scored:
    print(f"{score:.3f}   {chunk}")