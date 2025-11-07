import numpy as np


class Multiplier:
    def __init__(self, factor: float):
        self.factor = factor

    def apply(self, x: np.ndarray) -> np.ndarray:
        return x * self.factor


class Pipeline:
    def __init__(self, multiplier: Multiplier):
        self.multiplier = multiplier

    def process(self, x: np.ndarray) -> float:
        result = self.multiplier.apply(x)
        return float(np.mean(result))
