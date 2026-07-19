from __future__ import annotations

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


from types import SimpleNamespace

import pytest

from src.core.ext4 import Ext4Error, Inode


def test_get_inode_reports_the_non_directory_inode_without_name_error() -> None:
    non_directory = SimpleNamespace(is_dir=False, inode_idx=2)
    volume = SimpleNamespace(
        ignore_flags=False,
        get_inode=lambda _inode_idx, _file_type: non_directory,
    )
    root = SimpleNamespace(
        is_dir=True,
        inode_idx=1,
        volume=volume,
        open_dir=lambda _decode_name: iter((('child', 2, object()),)),
    )

    with pytest.raises(Ext4Error, match=r'Inode 2.*not a directory'):
        Inode.get_inode(root, 'child', 'grandchild')

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
