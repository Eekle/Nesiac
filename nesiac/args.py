import argparse
import pathlib
from typing import Optional
import glob


class Args:
    def __init__(self) -> None:
        _parser = argparse.ArgumentParser(
            prog="Nesiac",
        )

        _parser.add_argument("-elf_file", type=pathlib.Path)
        _parser.add_argument("-map_file", type=pathlib.Path)
        _parser.add_argument(
            "directory",
            help="The directory to search for map (.map) and elf (.elf, .out) files. "
            "Not necessary if the map and elf files are provided indivudally.",
            nargs="?",
            type=pathlib.Path,
        )
        _parsed_args = _parser.parse_args()
        efile = _parsed_args.elf_file  # type: Optional[pathlib.Path]
        mfile = _parsed_args.map_file  # type: Optional[pathlib.Path]
        dirpath = _parsed_args.directory  # type: Optional[pathlib.Path]
        if not efile and dirpath:
            globelf = glob.glob(str((dirpath / "*.elf").absolute()))
            globout = glob.glob(str((dirpath / "*.out").absolute()))
            glob_both = globelf + globout
            if len(glob_both) != 1:
                _parser.error(
                    "Elf file was not specified, and there is not "
                    "exactly one elf file in the given directory"
                )
            efile = pathlib.Path(glob_both[0])

        if not mfile and dirpath:
            globd = glob.glob(str((dirpath / "*.map").absolute()))
            if len(globd) != 1:
                _parser.error(
                    "Map file was not specified, and there is not "
                    "exactly one map file in the given directory",
                )
            mfile = pathlib.Path(globd[0])

        if not efile or not mfile:
            _parser.error(
                "If the map and elf files are not both specified, a search directory is required",
            )
        else:
            self._elf_file = efile  # type: pathlib.Path
            self._map_file = mfile  # type: pathlib.Path

    def elf_file(self) -> pathlib.Path:
        return self._elf_file

    def map_file(self) -> pathlib.Path:
        return self._map_file

    _map_text = None  # type: str | None

    def map_text(self) -> str:
        self._map_text = (
            self._map_text or open(self.map_file(), "r", encoding="utf-8").read()
        )
        return self._map_text
