
# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])

import io
import os
import shutil
import subprocess
import tarfile
import tempfile

import pytest

from src.core import PySquashfsImage


def _createFile(tarArchive, name, contents):
    tinfo = tarfile.TarInfo(name)
    tinfo.size = len(contents)
    tarArchive.addfile(tinfo, io.BytesIO(contents.encode()))


@pytest.mark.skipif(shutil.which('sqfstar') is None, reason='sqfstar is not installed')
@pytest.mark.parametrize("compression", ["", "gzip", "lz4", "lzma", "lzo", "xz", "zstd"])
def test_compressions(compression):
    with tempfile.TemporaryDirectory() as tmpdir:
        tarPath = os.path.join(tmpdir, "foo.tar")
        with tarfile.open(name=tarPath, mode='w:') as tarArchive:
            _createFile(tarArchive, "foo", "bar")

        squashfsPath = os.path.join(tmpdir, f"foo.{compression if compression else 'no-compression'}.squashfs")
        compressionOptions = ["-comp", compression] if compression else ["-noI", "-noId", "-noD", "-noF", "-noX"]
        process = subprocess.Popen(
            ["sqfstar"] + compressionOptions + [squashfsPath], stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        with open(tarPath, 'rb') as file:
            process.communicate(file.read())

        with open(squashfsPath, 'rb') as file, PySquashfsImage.SquashFsImage(file) as image:
            entries = list(iter(image))
            assert len(entries) == 2
            assert entries[0].path == "/"
            assert entries[1].path == "/foo"
            assert image.read_file(entries[1].inode) == b"bar"

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
