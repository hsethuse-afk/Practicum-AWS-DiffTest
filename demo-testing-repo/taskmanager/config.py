from typing import Self
class SortConfig:
    """Configuration class for sorting behavior"""

    def __init__(self: Self, algorithm: str="bubble", reverse_order: bool=False, stability_required: bool=True) -> None:
        self.algorithm = algorithm
        self.reverse_order = reverse_order
        self.stability_required = stability_required
        self.max_iterations = 1000

    def set_max_iterations(self: Self, value: int) -> Self:
        if value < 1:
            raise ValueError("Max iterations must be positive")
        self.max_iterations = value
        return self

    def __repr__(self):
        return f"SortConfig(algorithm={self.algorithm}, reverse={self.reverse_order}, stable={self.stability_required})"
