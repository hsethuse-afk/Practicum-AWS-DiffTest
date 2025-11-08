# impl_b.py
import numpy as np


class EmbeddingLayer:
    def __init__(self, vocab_size: int, dim: int, seed: int = 42):
        # Forgot to set seed — nondeterministic behavior
        self.embeddings = np.random.randn(vocab_size, dim)

    def embed(self, idx: int) -> np.ndarray:
        return self.embeddings[idx]
