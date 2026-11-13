from sentence_transformers import SentenceTransformer

sentences = ["The cat sat on the mat."]

# Loads from disk after the first run. The string is the model's name on Hugging Face.
model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(sentences)

print("type: ", type(embeddings))
print("shape:", embeddings.shape)   # how many numbers
print("first 8:", embeddings[:8])   # a peek at the actual values

