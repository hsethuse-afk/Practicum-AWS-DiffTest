# impl_a.py
import numpy as np


class FeatureExtractor:
    def __init__(self, kernel_size: int, normalize: bool = True):
        self.kernel_size = kernel_size
        self.normalize = normalize
        self.kernel = np.ones(kernel_size)
        if normalize:
            self.kernel /= np.sum(self.kernel)

    def apply(self, signal: np.ndarray) -> np.ndarray:
        return np.convolve(signal, self.kernel, mode="same")
