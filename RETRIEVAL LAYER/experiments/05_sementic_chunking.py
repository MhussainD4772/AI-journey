import re

import numpy as np
from sentence_transformers import SentenceTransformer


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


model = SentenceTransformer("all-MiniLM-L6-v2")

text = (
    "The tokenizer runs before the model. "
    "It converts text into a list of integers. "
    "The model never sees characters, only token IDs. "
    "Our deploy pipeline runs on GitHub Actions. "
    "Every merge to main triggers a build. "
    "The container image is pushed to ECR."
)

# Naive sentence split: break after . ! or ? followed by a space.
# Real text breaks this (Dr., e.g., version 2.5) — fine for now.
sentences = re.split(r"(?<=[.!?]) +", text.strip())

vectors = model.encode(sentences)

THRESHOLD = 0.3

print("adjacent sentence scores\n")

# Start the first chunk with the first sentence, then decide for each
# following sentence whether it joins this chunk or starts a new one.
chunks = [[sentences[0]]]

for i in range(len(sentences) - 1):
    score = cosine(vectors[i], vectors[i + 1])
    cut = score < THRESHOLD

    print(f"{score:.3f}  {'CUT ' if cut else '    '} {sentences[i + 1]}")

    if cut:
        chunks.append([sentences[i + 1]])
    else:
        chunks[-1].append(sentences[i + 1])

print(f"\n{len(chunks)} chunks\n")
for n, chunk in enumerate(chunks, 1):
    print(f"--- chunk {n} ---")
    print(" ".join(chunk) + "\n")