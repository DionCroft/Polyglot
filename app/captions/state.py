from dataclasses import dataclass


@dataclass(frozen=True)
class Caption:
    identifier: int
    start: float
    end: float
    english: str
    chinese: str = ""
    final: bool = False
    epoch: int = 0
    translation_status: str = "pending"
    source_language: str = "en"

    @property
    def source_text(self):
        return self.english if self.source_language == "en" else self.chinese

    @property
    def translated_text(self):
        return self.chinese if self.source_language == "en" else self.english
