# file: impl_b.py
class Counter:
    def __init__(self):
        self.count = 0

    def update(self, val: int) -> int:
        # Off-by-one difference
        self.count += val + 1
        return self.count
