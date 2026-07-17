from __future__ import annotations

import logging
import os
import sys
import threading
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

logger = logging.getLogger("mio.filesystem")
process_logger = logging.getLogger("mio.process.audit")

_ROOTS: set[Path] = set()
_EXCLUDED_ROOTS: set[Path] = set()
_INSTALLED = False
_GUARD = threading.local()
_READ_DEDUP_LOCK = threading.Lock()
_RECENT_READ_EVENTS: dict[tuple[object, ...], float] = {}
_READ_DEDUP_SECONDS = 0.5
_MAX_RECENT_READ_EVENTS = 512

_SPECIAL_DEVICE_NAMES = {
    "aux",
    "con",
    "nul",
    "prn",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}

_READ_EVENTS = {"os.listdir", "os.scandir"}
_MUTATION_EVENTS = {
    "os.chmod",
    "os.link",
    "os.mkdir",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.symlink",
    "os.truncate",
    "shutil.copyfile",
    "shutil.copymode",
    "shutil.copystat",
    "shutil.copytree",
    "shutil.move",
    "shutil.rmtree",
    "shutil.make_archive",
    "shutil.unpack_archive",
    "tempfile.mkdtemp",
    "tempfile.mkstemp",
}


def _normalize(path: object) -> Path | None:
    if isinstance(path, bytes):
        try:
            path = os.fsdecode(path)
        except UnicodeError:
            return None
    if not isinstance(path, (str, os.PathLike)):
        return None
    try:
        return Path(path).expanduser().absolute()
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def register_audit_root(path: str | os.PathLike[str]) -> None:
    normalized = _normalize(path)
    if normalized is not None:
        _ROOTS.add(normalized)


def exclude_audit_root(path: str | os.PathLike[str]) -> None:
    normalized = _normalize(path)
    if normalized is not None:
        _EXCLUDED_ROOTS.add(normalized)


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_relevant(path: Path) -> bool:
    if any(_is_inside(path, excluded) for excluded in _EXCLUDED_ROOTS):
        return False
    return any(_is_inside(path, root) for root in _ROOTS)


def _is_special_device_path(path: Path) -> bool:
    return path.name.casefold().split(".", 1)[0] in _SPECIAL_DEVICE_NAMES


def _is_runtime_executable(path: Path) -> bool:
    executable = _normalize(sys.executable)
    return executable is not None and path == executable


def _suppress_repeated_read(key: tuple[object, ...]) -> bool:
    now = time.monotonic()
    with _READ_DEDUP_LOCK:
        previous = _RECENT_READ_EVENTS.get(key)
        _RECENT_READ_EVENTS[key] = now
        if len(_RECENT_READ_EVENTS) > _MAX_RECENT_READ_EVENTS:
            cutoff = now - _READ_DEDUP_SECONDS
            stale = [
                stored_key
                for stored_key, timestamp in _RECENT_READ_EVENTS.items()
                if timestamp < cutoff
            ]
            for stored_key in stale:
                _RECENT_READ_EVENTS.pop(stored_key, None)
        return previous is not None and now - previous < _READ_DEDUP_SECONDS


def _open_is_mutating(mode: object, flags: object) -> bool:
    mode_text = str(mode or "")
    if any(marker in mode_text for marker in ("w", "a", "x", "+")):
        return True
    if not isinstance(flags, int):
        return False
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
    return bool(flags & write_flags)


def _path_values(event: str, args: tuple[Any, ...]) -> tuple[Path, ...]:
    two_path_events = {
        "os.link",
        "os.rename",
        "os.symlink",
        "shutil.copyfile",
        "shutil.copymode",
        "shutil.copystat",
        "shutil.copytree",
        "shutil.move",
        "shutil.unpack_archive",
    }
    indexes = (0, 1) if event in two_path_events else (0,)
    paths: list[Path] = []
    for index in indexes:
        if index >= len(args):
            continue
        normalized = _normalize(args[index])
        if normalized is not None and _is_relevant(normalized):
            paths.append(normalized)
    return tuple(paths)


def _guard_is_active() -> bool:
    try:
        return bool(_GUARD.active)
    except AttributeError:
        return False


def _emit_process_event(event: str, args: tuple[Any, ...]) -> bool:
    if event == "subprocess.Popen":
        executable = args[0] if args else None
        argv = args[1] if len(args) > 1 else ()
        cwd = args[2] if len(args) > 2 else None
        env = args[3] if len(args) > 3 else None
        try:
            argument_count = len(argv) if not isinstance(argv, str) else 1
        except TypeError:
            argument_count = 0
        env_keys = tuple(sorted(str(key) for key in env)) if isinstance(env, dict) else ()
        process_logger.info(
            "process.audit_spawn: executable=%r argument_count=%s cwd=%r env_keys=%r",
            executable,
            argument_count,
            cwd,
            env_keys,
        )
        return True
    if event == "os.system":
        command = args[0] if args else None
        process_logger.info(
            "process.audit_system: command_type=%s command_length=%s",
            type(command).__name__,
            len(command) if isinstance(command, (str, bytes)) else 0,
        )
        return True
    return False


def _emit(event: str, args: tuple[Any, ...]) -> None:
    if _guard_is_active():
        return
    if event in {"subprocess.Popen", "os.system"}:
        _GUARD.active = True
        try:
            _emit_process_event(event, args)
        finally:
            _GUARD.active = False
        return
    if event == "open":
        path = _normalize(args[0]) if args else None
        if (
            path is None
            or not _is_relevant(path)
            or _is_special_device_path(path)
        ):
            return
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else None
        mutating = _open_is_mutating(mode, flags)
        if not mutating:
            if _is_runtime_executable(path):
                return
            if _suppress_repeated_read(("open", path, mode, flags)):
                return
        _GUARD.active = True
        try:
            log_method = logger.info if mutating else logger.debug
            log_method(
                "filesystem.open: path=%s mode=%r flags=%r mutation=%s",
                path,
                mode,
                flags,
                mutating,
            )
        finally:
            _GUARD.active = False
        return

    if event not in _MUTATION_EVENTS and event not in _READ_EVENTS:
        return
    paths = _path_values(event, args)
    if not paths:
        return
    if event == "os.mkdir" and all(path.exists() for path in paths):
        return
    if event in _READ_EVENTS and _suppress_repeated_read((event, *paths)):
        return
    _GUARD.active = True
    try:
        log_method = logger.info if event in _MUTATION_EVENTS else logger.debug
        log_method(
            "filesystem.event: event=%s paths=%r args=%r",
            event,
            tuple(str(path) for path in paths),
            args[2:] if len(args) > 2 else (),
        )
    finally:
        _GUARD.active = False


def install_filesystem_audit(
    *,
    roots: Iterable[str | os.PathLike[str]],
    excluded_roots: Iterable[str | os.PathLike[str]] = (),
) -> None:
    global _INSTALLED
    for root in roots:
        register_audit_root(root)
    for root in excluded_roots:
        exclude_audit_root(root)
    if _INSTALLED:
        return
    sys.addaudithook(_emit)
    _INSTALLED = True
    logger.info(
        "filesystem.audit_installed: roots=%r excluded=%r",
        tuple(str(path) for path in sorted(_ROOTS)),
        tuple(str(path) for path in sorted(_EXCLUDED_ROOTS)),
    )


def audit_roots() -> tuple[str, ...]:
    return tuple(str(path) for path in sorted(_ROOTS))


__all__ = [
    "audit_roots",
    "exclude_audit_root",
    "install_filesystem_audit",
    "register_audit_root",
]
