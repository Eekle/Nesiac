from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryRegion:
    name: str
    origin: int
    length: int

    def contains_address(self, addr: int) -> bool:
        return self.origin <= addr < (self.origin + self.length)


def from_line(line: str) -> Optional[MemoryRegion]:
    pieces = line.split()
    if len(pieces) < 3:
        return None

    try:
        return MemoryRegion(
            name=pieces[0], origin=int(pieces[1], 16), length=int(pieces[2], 16)
        )
    except ValueError:
        return None


def from_text(text: str) -> list[MemoryRegion]:
    iter_lines = iter(text.splitlines())

    for line in iter_lines:
        if "Memory Configuration" in line:
            break

    next(iter_lines)
    next(iter_lines)

    regions = []  # type: list[MemoryRegion]
    for line in iter_lines:
        if reg := from_line(line):
            if reg.name != "*default*":
                regions.append(reg)
        else:
            break
    return regions
