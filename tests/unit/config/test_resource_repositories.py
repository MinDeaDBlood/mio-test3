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


import json
from pathlib import Path

from src.platform.json_file_repository import JsonFileRepository
from src.platform.language_repository import (
    language_file_path,
    list_language_names,
    read_language_map,
)
from src.core.cache_ops import calculate_directory_size, clear_directory


def test_json_file_repository_writes_complete_json_without_temp_residue(
    tmp_path: Path,
) -> None:
    target = tmp_path / "config" / "profiles.json"
    repository = JsonFileRepository(target)
    payload = {"profile": {"flag": True}}

    repository.write(payload)

    assert repository.exists() is True
    assert repository.read() == payload
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    assert not target.with_suffix(".json.tmp").exists()


def test_language_repository_lists_and_reads_root_language_files(
    tmp_path: Path,
) -> None:
    language_dir = tmp_path / "languages"
    language_dir.mkdir()
    (language_dir / "Russian.json").write_text(
        json.dumps({"hello": "Привет"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (language_dir / "English.json").write_text(
        json.dumps({"hello": "Hello"}),
        encoding="utf-8",
    )

    assert list_language_names(language_dir) == ("English", "Russian")
    assert language_file_path("Russian", base_path=tmp_path) == (
        language_dir / "Russian.json"
    )
    assert read_language_map("Russian", base_path=tmp_path) == {"hello": "Привет"}


def test_cache_operations_measure_and_clear_real_files(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    nested = cache_dir / "nested"
    nested.mkdir(parents=True)
    (cache_dir / "one.bin").write_bytes(b"1234")
    (nested / "two.bin").write_bytes(b"56789")

    assert calculate_directory_size(str(cache_dir)) == 9
    assert clear_directory(str(cache_dir)) == 0
    assert cache_dir.is_dir()
    assert tuple(cache_dir.iterdir()) == ()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
