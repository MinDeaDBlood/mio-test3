from __future__ import annotations

import os
import os.path as op
import subprocess
from dataclasses import dataclass
from os import name as osname, readlink, stat, walk
from pathlib import Path
from shutil import rmtree
from zipfile import BadZipFile, ZipFile, is_zipfile

from src.core.mtk_port.files import safe_extract_zip
from src.logic.common.service_output import ServiceOutput, build_service_output


class MtkPortOperationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MtkPortBinaries:
    make_ext4fs: str
    magiskboot: str
    img2simg: str

    @classmethod
    def from_tool_bin(cls, base_path: str | os.PathLike[str]) -> "MtkPortBinaries":
        suffix = ".exe" if os.name == "nt" else ""
        root = Path(base_path)
        return cls(
            make_ext4fs=str(root / f"make_ext4fs{suffix}"),
            magiskboot=str(root / f"magiskboot{suffix}"),
            img2simg=str(root / f"img2simg{suffix}"),
        )


class MtkOperationBase:
    def __init__(
        self,
        items: dict,
        bootimg: str,
        sysimg: str,
        portzip: str,
        genimg: bool = False,
        *,
        output: ServiceOutput | None = None,
        binaries: MtkPortBinaries,
        update_binary_path: str | os.PathLike[str],
        local_runtime_dir: str | os.PathLike[str],
    ) -> None:
        self.items = items
        self.output = output or build_service_output()
        self.binaries = binaries
        self.update_binary_path = Path(update_binary_path)
        self.local_runtime_dir = Path(local_runtime_dir)
        self.sysimg = sysimg
        self.bootimg = bootimg
        self.portzip = portzip
        self.genimg = genimg
        self.outdir = Path("out")
        self.outdir.mkdir(parents=True, exist_ok=True)
        if not self._inputs_exist:
            raise FileNotFoundError("One or more MTK port input files do not exist")
        self.sdat = False

    def _log(self, *parts: object, **kwargs) -> None:
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        text = sep.join(str(part) for part in parts)
        if end and text.endswith(end):
            text = text[: -len(end)]
        if text:
            self.output.log(text)

    @property
    def _inputs_exist(self) -> bool:
        return all(
            Path(path).exists() for path in (self.sysimg, self.bootimg, self.portzip)
        )

    def execv(self, cmd, verbose: bool = False) -> int:
        if verbose:
            self._log("Run command：\n", *cmd if isinstance(cmd, list) else cmd)
        creationflags = subprocess.CREATE_NO_WINDOW if osname == "nt" else 0
        try:
            result = subprocess.run(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
                check=False,
            )
        except OSError as exc:
            raise MtkPortOperationError(
                f"Cannot execute program {cmd!r}: {exc}"
            ) from exc
        output = result.stdout.decode("utf-8", errors="ignore")
        if verbose and output:
            self._log("Result：\n", output)
        if result.returncode != 0:
            detail = output.strip()
            message = f"Command failed with exit code {result.returncode}: {cmd!r}"
            if detail:
                message = f"{message}\n{detail}"
            raise MtkPortOperationError(message)
        return result.returncode

    def _decompress_portzip(self) -> None:
        outdir = Path("tmp/rom")
        if outdir.exists():
            rmtree(outdir)
        outdir.mkdir(parents=True)
        self._log("Unpacking port rom...")
        if not is_zipfile(self.portzip):
            raise BadZipFile(f"Port ROM is not a valid ZIP archive: {self.portzip}")
        with ZipFile(self.portzip, "r") as archive:
            safe_extract_zip(archive, outdir)

    @staticmethod
    def _pack_fit_size() -> float:
        total = 0
        for root, _dirs, files in walk("tmp/rom/system"):
            for file_name in files:
                total += stat(op.join(root, file_name)).st_size
        return total * 1.2

    @staticmethod
    def _readlink(dest: str) -> str | None:
        if osname == "nt":
            with open(dest, "rb") as stream:
                if stream.read(10) == b"!<symlink>":
                    return stream.read().decode("utf-16").rstrip("\0")
                return None
        try:
            return readlink(dest)
        except OSError:
            return None

    def clean(self) -> None:
        self._log("Port Done, Cleaning Temp...")
        if Path("tmp").exists():
            rmtree("tmp")


__all__ = ["MtkOperationBase", "MtkPortBinaries", "MtkPortOperationError"]
