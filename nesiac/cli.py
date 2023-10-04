import time
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.console import Group, Console
from typing import Optional
from . import ingest
from .args import Args
import os

if os.name == "nt":
    import msvcrt
    def get_key() -> Optional[int]:
        if msvcrt.kbhit():
            return msvcrt.getch()[0]
        else:
            return None
else:
    import getchlib
    def get_key() -> Optional[int]:
        stkey = getchlib.getkey(False) # type: Optional[str]
        if stkey and len(stkey) == 1:
            return ord(stkey)
        return None

class InteractiveRegions:
    def __init__(self, reg: list[ingest.RegionWithSections]) -> None:
        self.regions = reg
        self.r_ix = 0
        self.s_ix = 0
        self.object_page = 0
        self.objects_per_page = 25
        if len(self.selected_region().children) == 0:
            self._next_region_with_children()

    def update_objs_per_page(self, con: Console):
        old = self.objects_per_page
        self.objects_per_page = con.height - 10
        if old != self.objects_per_page:
            self.object_page = 0

    def selected_region(self) -> ingest.RegionWithSections:
        return self.regions[self.r_ix]

    def selected_section(self) -> ingest.SectionWithObjects:
        return self.selected_region().children[self.s_ix]

    def _next_region_with_children(self) -> bool:
        for ix in range(self.r_ix + 1, len(self.regions)):
            if len(self.regions[ix].children):
                self.r_ix = ix
                return True
        return False

    def _prev_region_with_children(self) -> bool:
        for ix in reversed(range(0, self.r_ix)):
            if len(self.regions[ix].children):
                self.r_ix = ix
                return True
        return False

    def next_section(self):
        # Advance to this region's next child if possible
        if (self.s_ix + 1) < len(self.selected_region().children):
            self.s_ix += 1
            self.object_page = 0
        else:
            # Otherwise move to the next region if possible
            if (self.r_ix + 1) < len(self.regions):
                if self._next_region_with_children():
                    self.s_ix = 0
                    self.object_page = 0

    def objects_in_view(self):
        return self.selected_section().children[
            self.object_page
            * self.objects_per_page : (self.object_page + 1)
            * self.objects_per_page
        ]

    def next_object_page(self):
        if ((self.object_page + 1) * self.objects_per_page) < len(
            self.selected_section().children
        ):
            self.object_page += 1

    def prev_object_page(self):
        if self.object_page > 0:
            self.object_page -= 1

    def prev_section(self):
        if self.s_ix > 0:
            self.s_ix -= 1
            self.object_page = 0
        else:
            if self.r_ix > 0:
                if self._prev_region_with_children():
                    self.s_ix = len(self.selected_region().children) - 1
                    self.object_page = 0

    def reg_section_text(self, reg: ingest.RegionWithSections) -> Text:
        fullness = reg.used_mem() / reg.data.length
        if fullness > 0.9:
            pc_colour = "bright_red"
        elif fullness > 0.75:
            pc_colour = "bright_magenta"
        else:
            pc_colour = ""

        return Text.assemble(
            (reg.data.name, ""),
            " ",
            (f"{fullness:.0%}", pc_colour),
            style="on dark_blue" if reg == self.selected_region() else "",
            no_wrap=True,
        )

    def reg_totals_text(self, reg: ingest.RegionWithSections) -> Text:
        used_size = reg.used_mem()
        used_size_str = size_display(used_size)
        total_size_str = size_display(reg.data.length)
        return Text.assemble(
            (f"{used_size/reg.data.length:.0%}".ljust(4), "bright_green"),
            " | ",
            (f"{used_size_str}".rjust(6), "bright_yellow"),
            " of ",
            (f"{total_size_str}", "bright_yellow"),
        )

    def section_text(self, sec: ingest.SectionWithObjects, total_size: int) -> Text:
        return Text.assemble(
            (f"{sec.data.size/total_size:.0%}".ljust(4), "green"),
            " | ",
            (f"{size_display(sec.data.size)}".rjust(6), "yellow"),
            " | ",
            sec.data.name,
            style="on dark_blue" if sec == self.selected_section() else "",
            no_wrap=True,
        )


def size_display(numbytes: int) -> str:
    megabyte = 1024 * 1024
    kilobyte = 1024
    if numbytes > megabyte:
        fval = numbytes / megabyte
        symbol = "M"
    elif numbytes > (kilobyte):
        fval = numbytes / kilobyte
        symbol = "K"
    else:
        return f"{numbytes} B"

    fmt_options = [
        f"{int(fval)}",
        f"{fval:.1f}",
        f"{fval:.2f}",
    ]

    chosen_format = max([f for f in fmt_options if len(f) <= 4], key=len)
    return chosen_format + " " + symbol


def cli() -> None:
    o_data = InteractiveRegions(ingest.ingest())

    def region_view(data: InteractiveRegions) -> Group:
        title = Text.assemble(
            str(Args().elf_file().parts[-1]),
            ", ",
            str(Args().map_file().parts[-1]),
            style="bright_green",
        )
        treeitems = []  # type: list[Tree]
        for reg in data.regions:
            reg_tree = Tree(o_data.reg_section_text(reg), guide_style="bright_black")
            for sec in reg.children:
                reg_tree.add(o_data.section_text(sec, reg.data.length))
            reg_tree.add(o_data.reg_totals_text(reg))
            treeitems.append(reg_tree)
        return Group(title, *treeitems)

    def obj_view(data: InteractiveRegions) -> Table:
        numpages = int(
            1 + (len(data.selected_section().children) / data.objects_per_page)
        )
        table = Table(
            title=f"{data.selected_section().data.name} (Page {data.object_page + 1}/{numpages})",
            row_styles=["", "dim"],
            title_justify="left",
        )
        table.add_column("Size", justify="right", style="yellow", width=6)
        table.add_column("Address", justify="right", width=10)
        table.add_column("Symbol Name")
        for obj in data.objects_in_view():
            table.add_row(size_display(obj.size), f"{obj.addr:#010x}", obj.name)

        return table

    def whole_thing(data: InteractiveRegions) -> Layout:
        grid = Table.grid()
        grid.add_column()
        grid.add_column()
        grid.add_row(
            region_view(data),
            obj_view(data),
        )
        grid.padding = 2
        layout = Layout()

        layout.split_column(
            Layout(name="u"),
            Layout(
                name="l",
                size=1,
            ),
        )

        layout["u"].update(grid)
        layout["l"].update(
            Text(
                "  W/S: Move between sections | E/D: Scroll symbol table | Esc: Exit  ",
                style="black on white",
            ),
        )
        return layout

    with Live(Layout(), auto_refresh=False) as live:
        last_size = live.console.size
        o_data.update_objs_per_page(live.console)
        live.update(whole_thing(o_data), refresh=True)
        while True:

            if key := get_key():
                if key == ord('w'):
                    o_data.prev_section()
                    live.update(whole_thing(o_data), refresh=True)
                elif key == ord('s'):
                    o_data.next_section()
                    live.update(whole_thing(o_data), refresh=True)
                elif key == ord('e'):
                    o_data.prev_object_page()
                    live.update(whole_thing(o_data), refresh=True)
                elif key == ord('d'):
                    o_data.next_object_page()
                    live.update(whole_thing(o_data), refresh=True)
                elif key == 27:  # Escape
                    live.update("", refresh=True)
                    exit(0)
            else:
                if live.console.size != last_size:
                    last_size = live.console.size
                    o_data.update_objs_per_page(live.console)
                    live.update(whole_thing(o_data), refresh=True)
                time.sleep(5e-3)


if __name__ == "__main__":
    cli()
