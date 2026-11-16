import numpy as np

def cosine(a,b):
    """Angle between two vectors, ignoring their lengths."""
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

a = np.array([10, 0])
b = np.array([1, 6])      # same direction
c = np.array([12, 1])      # perpendicular
d = np.array([-1, 0])     # opposite
e = np.array([14, 0])     # same direction as a, ten times longer

print("a vs b (identical):       ", cosine(a, b))
print("a vs c (perpendicular):   ", cosine(a, c))
print("a vs d (opposite):        ", cosine(a, d))
print("a vs e (same dir, longer):", cosine(a, e))