# file: impl_b.py
class TextProcessor:
    def __init__(self):
        pass

    def process(self, text: str) -> str:
        # Only lowercase, doesn’t trim (slightly different)
        return text.lower()
