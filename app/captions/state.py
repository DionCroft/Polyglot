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
