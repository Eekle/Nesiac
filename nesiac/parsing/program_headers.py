from dataclasses import dataclass


@dataclass
class ProgramHeader:
    typ: str
    v_addr: int
    load_addr: int
    size: int
