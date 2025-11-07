class Normalizer:
    def __init__(self, to_lower=True, strip_spaces=True):
        # Slight difference: ignores strip_spaces argument
        self.to_lower = to_lower
        self.strip_spaces = False

    def normalize(self, text: str) -> str:
        if self.strip_spaces:
            text = text.strip()
        if self.to_lower:
            text = text.lower()
        return text


class TextPipeline:
    def __init__(self, normalizer: Normalizer):
        self.normalizer = normalizer

    def process(self, text: str) -> str:
        return self.normalizer.normalize(text)
