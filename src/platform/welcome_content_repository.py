from __future__ import annotations

from pathlib import Path

from src.platform.language_repository import list_language_names
from src.platform.runtime_paths import LANGUAGE_DIR, LICENSE_DIR


class WelcomeResourceError(RuntimeError):
    """Raised when a required welcome resource is missing or unreadable."""


class WelcomeContentRepository:
    """Read language and license resources required by the welcome wizard."""

    def __init__(
        self,
        *,
        language_directory: str | Path = LANGUAGE_DIR,
        license_directory: str | Path = LICENSE_DIR,
    ) -> None:
        self.language_directory = Path(language_directory)
        self.license_directory = Path(license_directory)

    def list_languages(self) -> tuple[str, ...]:
        try:
            return list_language_names(self.language_directory)
        except FileNotFoundError as exc:
            raise WelcomeResourceError(
                f"Welcome language directory is missing: {self.language_directory}"
            ) from exc

    def list_licenses(self) -> tuple[str, ...]:
        directory = self.license_directory
        if not directory.is_dir():
            raise WelcomeResourceError(
                f"Welcome license directory is missing: {directory}"
            )
        return tuple(
            sorted(
                path.stem
                for path in directory.iterdir()
                if path.is_file() and path.name != "private.txt"
            )
        )

    def read_license(self, license_name: str) -> str:
        if not license_name:
            raise ValueError("License name is required.")
        path = self.license_directory / f"{license_name}.txt"
        if not path.is_file():
            raise WelcomeResourceError(f"Welcome license file is missing: {path}")
        return path.read_text(encoding="utf-8")

    def read_private_notice(self) -> str:
        path = self.license_directory / "private.txt"
        if not path.is_file():
            raise WelcomeResourceError(f"Welcome private notice is missing: {path}")
        return path.read_text(encoding="utf-8")


__all__ = ["WelcomeContentRepository", "WelcomeResourceError"]
