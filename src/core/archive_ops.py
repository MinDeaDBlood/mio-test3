from __future__ import annotations

from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def write_zip_entries(
    output_path: str | PathLike[str],
    *,
    text_entries: Mapping[str, str] | None = None,
    file_entries: Mapping[str, str | PathLike[str]] | None = None,
) -> Path:
    """Write a ZIP from explicit in-memory text and existing source files."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for archive_name, text in sorted((text_entries or {}).items()):
            archive.writestr(archive_name, text)
        for archive_name, source_path in sorted((file_entries or {}).items()):
            archive.write(Path(source_path), arcname=archive_name)
    return destination


__all__ = ["write_zip_entries"]
