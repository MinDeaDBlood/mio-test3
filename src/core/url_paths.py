from __future__ import annotations

from urllib.parse import unquote, urlsplit


def download_filename(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValueError('Download URL is empty')
    filename = unquote(urlsplit(normalized).path.rsplit('/', 1)[-1]).strip()
    if not filename or filename in {'.', '..'}:
        raise ValueError('Download URL has no file name')
    if '/' in filename or '\\' in filename or '\x00' in filename:
        raise ValueError('Download URL contains an invalid file name')
    return filename


__all__ = ['download_filename']
