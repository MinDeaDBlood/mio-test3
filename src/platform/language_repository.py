from __future__ import annotations

from pathlib import Path

from src.platform.runtime_paths import LANGUAGE_DIR
from src.core.json_store import JsonEdit


def language_file_path(
    language_name: str,
    *,
    base_path: str | Path | None = None,
) -> Path:
    directory = LANGUAGE_DIR if base_path is None else Path(base_path) / "languages"
    return directory / f"{language_name}.json"


def list_language_names(
    language_dir: str | Path = LANGUAGE_DIR,
) -> tuple[str, ...]:
    directory = Path(language_dir)
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    return tuple(
        sorted(path.stem for path in directory.glob("*.json") if path.is_file())
    )


def read_language_map(
    language_name: str,
    *,
    base_path: str | Path | None = None,
) -> dict[str, object]:
    path = language_file_path(language_name, base_path=base_path)
    if not path.is_file():
        raise FileNotFoundError(f"Language file not found: {path}")
    data = JsonEdit(str(path)).read()
    if not isinstance(data, dict):
        raise TypeError(f"Language file is not a mapping: {path}")
    return data


__all__ = [
    "language_file_path",
    "list_language_names",
    "read_language_map",
]
