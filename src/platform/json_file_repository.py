from __future__ import annotations

import json
from pathlib import Path


class JsonFileRepository:
    """Read and atomically replace one UTF-8 JSON resource file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.is_file()

    def read(self) -> object:
        with self.path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    def write(self, value: object) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with temporary_path.open("w", encoding="utf-8", newline="\n") as file_handle:
            json.dump(value, file_handle, indent=4, ensure_ascii=False)
            file_handle.write("\n")
        temporary_path.replace(self.path)


__all__ = ["JsonFileRepository"]
