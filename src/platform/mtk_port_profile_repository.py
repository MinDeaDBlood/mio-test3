from __future__ import annotations

from pathlib import Path
from typing import Any

from src.platform.json_file_repository import JsonFileRepository
from src.platform.runtime_paths import MTK_PORT_PROFILES_FILE


class MtkPortProfileRepository:
    """Persist the user-editable MTK profile mapping without domain decisions."""

    def __init__(self, path: Path = MTK_PORT_PROFILES_FILE) -> None:
        self._path = Path(path)
        self._repository = JsonFileRepository(self._path)

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._repository.exists()

    def load(self) -> dict[str, dict[str, Any]]:
        value = self._repository.read()
        if not isinstance(value, dict):
            raise TypeError(f"MTK profile file must contain a JSON object: {self._path}")
        return value

    def save(self, profiles: dict[str, dict[str, Any]]) -> None:
        self._repository.write(profiles)


__all__ = ["MtkPortProfileRepository"]
