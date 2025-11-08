import numpy as np


class Multiplier:
    def __init__(self, factor: float):
        # Subtle bug: store wrong factor (off by 1)
        self.factor = factor + 1

    def apply(self, x: np.ndarray) -> np.ndarray:
        return x * self.factor


class Pipeline:
    def __init__(self, multiplier: Multiplier):
        self.multiplier = multiplier

    def process(self, x: np.ndarray) -> float:
        result = self.multiplier.apply(x)
        # Same mean operation
        return float(np.mean(result))
