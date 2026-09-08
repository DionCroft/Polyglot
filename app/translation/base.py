from typing import Protocol


class TranslationBackend(Protocol):
    def translate(self, text: str) -> str: ...
