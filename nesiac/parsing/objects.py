from dataclasses import dataclass
import pathlib
from elftools.elf.elffile import ELFFile, SymbolTableSection
import cxxfilt
import rust_demangler


@dataclass(frozen=True)
class ElfObject:
    addr: int
    size: int
    name: str


def _demangle(input: str) -> str:
    try:
        rust_d = rust_demangler.demangle(input)
    except Exception:
        rust_d = None
    try:
        cpp_d = cxxfilt.demangle(input)
    except Exception:
        cpp_d = None
    return rust_d or cpp_d or input


def from_elf(file: pathlib.Path) -> list[ElfObject]:
    outlist = []  # type: list[ElfObject]
    with open(file, "rb") as in_f:
        elf = ELFFile(in_f)
        symtab = elf.get_section_by_name(".symtab")
        if not isinstance(symtab, SymbolTableSection):
            return outlist
        for sym in symtab.iter_symbols():
            if sym.entry.st_info.type in ["STT_OBJECT", "STT_FUNC"]:
                outlist.append(
                    ElfObject(sym.entry.st_value, sym.entry.st_size,
                              _demangle(sym.name))
                )
    return outlist
