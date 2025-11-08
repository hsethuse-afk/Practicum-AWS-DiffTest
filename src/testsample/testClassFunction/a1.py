# file: impl_a.py
class TextProcessor:
    def __init__(self):
        pass

    def process(self, text: str) -> str:
        # Trim spaces and make lowercase
        return text.strip().lower()
