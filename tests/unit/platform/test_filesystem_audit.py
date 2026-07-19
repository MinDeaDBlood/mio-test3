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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])

import logging
import os
import shutil
from pathlib import Path

import src.platform.filesystem_audit as audit


def test_open_mutation_detection() -> None:
    assert audit._open_is_mutating("wb", None) is True
    assert audit._open_is_mutating("r", None) is False
    assert audit._open_is_mutating(None, os.O_CREAT | os.O_WRONLY) is True


def test_registered_root_filters_unrelated_paths(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit.register_audit_root(root)

    assert audit._is_relevant(root / "project" / "file.img") is True
    assert audit._is_relevant(tmp_path / "outside.img") is False


def test_mutating_event_is_logged(caplog, tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "output.img"
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit.register_audit_root(root)

    with caplog.at_level(logging.INFO, logger="mio.filesystem"):
        audit._emit("open", (str(target), "wb", os.O_CREAT | os.O_WRONLY))

    assert "filesystem.open" in caplog.text
    assert "mutation=True" in caplog.text


def test_runtime_executable_reads_are_not_logged(
    caplog, tmp_path: Path, monkeypatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    executable = root / "tool.exe"
    executable.write_bytes(b"binary")
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit._RECENT_READ_EVENTS.clear()
    audit.register_audit_root(root)
    monkeypatch.setattr(audit.sys, "executable", str(executable))

    with caplog.at_level(logging.DEBUG, logger="mio.filesystem"):
        audit._emit("open", (str(executable), "r", os.O_RDONLY))

    assert "filesystem.open" not in caplog.text


def test_repeated_read_events_are_collapsed(caplog, tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "settings.json"
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit._RECENT_READ_EVENTS.clear()
    audit.register_audit_root(root)

    with caplog.at_level(logging.DEBUG, logger="mio.filesystem"):
        audit._emit("open", (str(target), "r", os.O_RDONLY))
        audit._emit("open", (str(target), "r", os.O_RDONLY))

    assert caplog.text.count("filesystem.open") == 1


def test_existing_directory_mkdir_is_not_logged(caplog, tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit.register_audit_root(root)

    with caplog.at_level(logging.INFO, logger="mio.filesystem"):
        audit._emit("os.mkdir", (str(root), 0o777, -1))

    assert "os.mkdir" not in caplog.text


def test_subprocess_audit_logs_metadata_without_environment_values(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="mio.process.audit"):
        audit._emit(
            "subprocess.Popen",
            ("tool.exe", ["tool.exe", "--run"], "/workspace", {"TOKEN": "secret"}),
        )

    assert "process.audit_spawn" in caplog.text
    assert "TOKEN" in caplog.text
    assert "secret" not in caplog.text


def test_copy_event_logs_relevant_destination_when_source_is_external(
    caplog, tmp_path: Path
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    destination = root / "copied.img"
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit.register_audit_root(root)

    with caplog.at_level(logging.INFO, logger="mio.filesystem"):
        audit._emit(
            "shutil.copyfile",
            (str(tmp_path / "external.img"), str(destination)),
        )

    matching_records = [
        record
        for record in caplog.records
        if record.name == "mio.filesystem"
        and record.args
        and record.args[0] == "shutil.copyfile"
    ]
    assert len(matching_records) == 1
    assert str(destination) in matching_records[0].args[1]


def test_real_file_lifecycle_is_logged_by_installed_audit_hook(
    caplog, tmp_path: Path
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    audit._ROOTS.clear()
    audit._EXCLUDED_ROOTS.clear()
    audit.install_filesystem_audit(roots=(root,))

    source = root / "source.txt"
    copied = root / "copied.txt"
    moved = root / "moved.txt"
    nested = root / "nested"

    with caplog.at_level(logging.DEBUG):
        source.write_text("content", encoding="utf-8")
        shutil.copyfile(source, copied)
        shutil.move(copied, moved)
        nested.mkdir()
        moved.unlink()
        nested.rmdir()
        source.unlink()

    text = caplog.text
    assert "filesystem.open" in text
    assert "shutil.copyfile" in text
    assert "shutil.move" in text or "os.rename" in text
    assert "os.mkdir" in text
    assert "os.remove" in text
    assert "os.rmdir" in text


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
