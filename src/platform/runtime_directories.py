from __future__ import annotations

from pathlib import Path

from src.platform.runtime_paths import (
    LOG_DIR,
    MAGISK_TEMP_DIR,
    MTK_PORT_TEMP_DIR,
    PLUGIN_DOWNLOAD_DIR,
    PLUGIN_INSTALL_DIR,
    PLUGIN_RUNTIME_DIR,
    TEMP_DIR,
    UPDATE_TEMP_DIR,
)

RUNTIME_DIRECTORIES = (
    LOG_DIR,
    TEMP_DIR,
    PLUGIN_DOWNLOAD_DIR,
    PLUGIN_RUNTIME_DIR,
    UPDATE_TEMP_DIR,
    LOG_DIR,
    MAGISK_TEMP_DIR,
    MTK_PORT_TEMP_DIR,
    PLUGIN_INSTALL_DIR,
)


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def prepare_log_files(log_dir: str | Path, log_file: str | Path) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    Path(log_file).touch()


def ensure_runtime_directories() -> tuple[Path, ...]:
    for path in RUNTIME_DIRECTORIES:
        path.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIRECTORIES


__all__ = ["RUNTIME_DIRECTORIES", "ensure_directory", "ensure_runtime_directories", "prepare_log_files"]
