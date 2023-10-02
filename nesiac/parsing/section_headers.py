from dataclasses import dataclass


@dataclass(frozen=True)
class SectionHeader:
    name: str
    type: str
    addr: int
    size: int
