from dataclasses import replace
from elftools.elf.elffile import ELFFile
from elftools.elf.elffile import Section, Segment

from .parsing import (
    program_headers,
    map_regions,
    section_headers,
    objects,
)
from .args import Args


class SectionWithObjects:
    data: section_headers.SectionHeader
    children: list[objects.ElfObject]

    def __init__(self, sec: section_headers.SectionHeader) -> None:
        self.data = sec
        self.children = []

    def add_object(self, obj: objects.ElfObject):
        self.children.append(obj)

    def into_load_section(self, offset: int) -> "SectionWithObjects":
        other = SectionWithObjects(
            sec=replace(
                self.data, name=self.data.name + " (L)", addr=self.data.addr + offset
            )
        )
        other.children = list(self.children)
        return other


class RegionWithSections:
    data: map_regions.MemoryRegion
    children: list[SectionWithObjects]

    def __init__(self, reg: map_regions.MemoryRegion) -> None:
        self.data = reg
        self.children = []

    def add_section(self, sec: SectionWithObjects):
        self.children.append(sec)

    def used_mem(self) -> int:
        return sum(sec.data.size for sec in self.children)


def ingest() -> list[RegionWithSections]:
    args = Args()
    regions = list(map(RegionWithSections, map_regions.from_text(args.map_text())))

    def into_my_section_type(sec: Section) -> SectionWithObjects | None:
        # Check if the section takes up space in the binary
        if (sec.header.sh_flags & 2) == 0:
            return None
        return SectionWithObjects(
            section_headers.SectionHeader(
                sec.name, sec.header.sh_type, sec.header.sh_addr, sec.header.sh_size
            )
        )

    def into_my_header_type(seg: Segment) -> program_headers.ProgramHeader:
        return program_headers.ProgramHeader(
            load_addr=seg.header.p_paddr,
            v_addr=seg.header.p_vaddr,
            size=seg.header.p_memsz,
            typ=seg.header.p_type,
        )

    with open(args.elf_file(), "rb") as elff:
        elf = ELFFile(elff)

        p_hdrs = list(map(into_my_header_type, elf.iter_segments()))
        sections = [
            sec
            for sec in map(into_my_section_type, elf.iter_sections())
            if sec is not None
        ]

        for p_h in p_hdrs:
            if p_h.load_addr != p_h.v_addr:
                new_sections = []  # type: list[SectionWithObjects]
                for section in sections:
                    if section.data.type == "SHT_PROGBITS":
                        if p_h.v_addr <= section.data.addr < (p_h.v_addr + p_h.size):
                            new_sections.append(
                                section.into_load_section(p_h.load_addr - p_h.v_addr)
                            )
                sections.extend(new_sections)

    objs = objects.from_elf(args.elf_file())

    # objs = objects.from_text(external_cmds.elf_objects(args.elf_file()))

    for obj in objs:
        try:
            next(
                s
                for s in sections
                if (s.data.addr <= obj.addr < (s.data.addr + s.data.size))
            ).add_object(obj)
        except StopIteration:
            # Not in a physical section, which is fine
            pass

    for sec in sections:
        for reg in regions:
            if reg.data.contains_address(sec.data.addr):
                reg.add_section(sec)

    for reg in regions:
        reg.children.sort(key=lambda x: x.data.size, reverse=True)
        for sec in reg.children:
            sec.children.sort(key=lambda x: x.size, reverse=True)

    return regions
