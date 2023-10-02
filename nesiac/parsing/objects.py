from dataclasses import dataclass
import pathlib
from elftools.elf.elffile import ELFFile, SymbolTableSection
from cpp_demangle import demangle

@dataclass(frozen=True)
class ElfObject:
    addr: int
    size: int
    name: str


def from_elf(file: pathlib.Path) -> list[ElfObject]:
    outlist = []  # type: list[ElfObject]
    with open(file, "rb") as in_f:
        elf = ELFFile(in_f)
        symtab = elf.get_section_by_name(".symtab")
        if not isinstance(symtab, SymbolTableSection):
            return outlist
        for sym in symtab.iter_symbols():
            if sym.entry.st_info.type in ["STT_OBJECT", "STT_FUNC"]:
                try:
                    name = demangle(sym.name)
                except ValueError:
                    name = sym.name
                outlist.append(
                    ElfObject(sym.entry.st_value, sym.entry.st_size, name)
                )
    return outlist
