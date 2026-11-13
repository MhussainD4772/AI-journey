from sentence_transformers import SentenceTransformer
import numpy as np


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


model = SentenceTransformer("all-MiniLM-L6-v2")

base = "The cat sat on the mat."
others = [
    "A kitten rested on the rug.",       # same meaning, almost no shared words
    "A kitten was pushed on the ride.",    # related topic
    "I need to refinance my mortgage.",  # unrelated
]

# One call for all four. Row 0 is the base, rows 1-3 are the others.
vectors = model.encode([base] + others)

print(f'base: "{base}"\n')
for sentence, vector in zip(others, vectors[1:]):
    print(f"{cosine(vectors[0], vector):.3f}   {sentence}")