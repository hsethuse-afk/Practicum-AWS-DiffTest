# impl_b.py
import numpy as np


class FeatureExtractor:
    def __init__(self, kernel_size: int, normalize: bool = True):
        self.kernel_size = kernel_size
        self.normalize = normalize
        self.kernel = np.ones(kernel_size)
        # Bug: forgets to normalize the kernel
        # So the convolution result is scaled up by kernel_size
        # even though the interface matches

    def apply(self, signal: np.ndarray) -> np.ndarray:
        return np.convolve(signal, self.kernel, mode="same")
