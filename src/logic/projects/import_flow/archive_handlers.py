"""Archive extraction helpers for project import flow.

This module owns low-level archive mechanics so the import orchestration service
can stay focused on project/runtime state transitions. ZIP extraction is done
manually instead of through ``ZipFile.extract`` so unsafe member paths cannot
escape the project directory.
"""

from __future__ import annotations

import gzip
import os
import shutil
import stat
import zipfile
from collections.abc import Callable

ChunkWriter = Callable[[str], None]
ErrorHandler = Callable[[str, Exception], None]


class UnsafeArchiveMemberError(ValueError):
    """Raised when an archive member would escape the target directory."""



def strip_gzip_suffix(path: str) -> str:
    """Return the output basename for a gzip payload."""
    output_file_name = os.path.basename(path)
    return output_file_name[:-3] if output_file_name.endswith('.gz') else output_file_name



def extract_gzip_payload(source_path: str, target_path: str, *, chunk_size: int = 8192) -> None:
    """Extract one gzip stream into *target_path* without loading it all at once."""
    with open(target_path, 'wb') as output, gzip.open(source_path, 'rb') as input_file:
        while True:
            data = input_file.read(chunk_size)
            if not data:
                break
            output.write(data)



def decode_zip_member_name(member_name: str) -> str:
    """Decode legacy ROM zip names that are often stored as cp437 bytes."""
    try:
        return member_name.encode('cp437').decode('gbk')
    except UnicodeError:
        try:
            return member_name.encode('cp437').decode('utf-8')
        except UnicodeError:
            return member_name



def _is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    """Return True for Unix symlink entries encoded in ZIP metadata."""
    return stat.S_ISLNK((info.external_attr >> 16) & 0o170000)



def _safe_member_parts(member_name: str) -> tuple[str, ...]:
    """Normalize a ZIP member path and reject absolute/traversal paths."""
    normalized = member_name.replace('\\', '/')
    drive, _tail = os.path.splitdrive(normalized)
    if drive or normalized.startswith('/'):
        raise UnsafeArchiveMemberError(f'Unsafe absolute archive member: {member_name!r}')
    parts = tuple(part for part in normalized.split('/') if part and part != '.')
    if any(part == '..' for part in parts):
        raise UnsafeArchiveMemberError(f'Unsafe traversal archive member: {member_name!r}')
    return parts



def _safe_target_path(target_dir: str, member_name: str) -> str:
    """Build a target path for a safe archive member name."""
    parts = _safe_member_parts(member_name)
    if not parts:
        raise UnsafeArchiveMemberError(f'Empty archive member: {member_name!r}')
    return os.path.join(target_dir, *parts)



def _extract_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, target_dir: str, decoded_name: str) -> None:
    """Extract one ZIP entry after validating original and decoded paths."""
    if _is_zip_symlink(info):
        raise UnsafeArchiveMemberError(f'Unsafe symlink archive member: {info.filename!r}')
    _safe_member_parts(info.filename)
    target_path = _safe_target_path(target_dir, decoded_name)
    if info.is_dir():
        os.makedirs(target_path, exist_ok=True)
        return
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with archive.open(info, 'r') as input_file, open(target_path, 'wb') as output_file:
        shutil.copyfileobj(input_file, output_file)



def extract_zip_members(
    zip_path: str,
    target_dir: str,
    *,
    on_member: ChunkWriter,
    on_error: ErrorHandler,
) -> None:
    """Extract a ROM zip archive and preserve decoded member names.

    ``on_member`` and ``on_error`` keep UI/logging outside this low-level helper.
    Unsafe ZIP paths are reported through ``on_error`` and skipped.
    """
    with zipfile.ZipFile(zip_path, 'r') as archive:
        for info in archive.infolist():
            decoded_name = decode_zip_member_name(info.filename)
            try:
                _extract_zip_member(archive, info, target_dir, decoded_name)
            except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
                on_error(decoded_name, exc)
            else:
                on_member(decoded_name)


__all__ = [
    'UnsafeArchiveMemberError',
    'decode_zip_member_name',
    'extract_gzip_payload',
    'extract_zip_members',
    'strip_gzip_suffix',
]
