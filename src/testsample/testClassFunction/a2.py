# file: impl_a.py
class Counter:
    def __init__(self):
        self.count = 0

    def update(self, val: int) -> int:
        self.count += val
        return self.count
