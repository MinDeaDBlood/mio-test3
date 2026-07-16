from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ENCRYPTION_FLAGS_TO_REMOVE_BY_PREFIX = (
    'forceencrypt=',
    'forcefdeorfbe=',
    'fileencryption=',
    'metadata_encryption=',
    'keydirectory=',
)
ENCRYPTION_FLAGS_TO_REMOVE_EXACT = {
    'forceencrypt',
    'forcefdeorfbe',
    'encryptable',
    'fileencryption',
    'metadata_encryption',
}


@dataclass(frozen=True)
class EncryptionPatchResult:
    path: Path
    modified: bool
    encoding: str
    modified_lines: int


def clean_encryption_flags_preserve_format(options_part: str) -> tuple[str, bool]:
    value = options_part
    modified = False
    for prefix in ENCRYPTION_FLAGS_TO_REMOVE_BY_PREFIX:
        pattern = rf'(?i)(,\s*|\s+){re.escape(prefix)}[^\s,]*'
        if re.search(pattern, value):
            value = re.sub(pattern, '', value)
            modified = True
    for flag in ENCRYPTION_FLAGS_TO_REMOVE_EXACT:
        pattern = rf'(?i)(,\s*|\s+)\b{re.escape(flag)}\b'
        if re.search(pattern, value):
            value = re.sub(pattern, '', value)
            modified = True
    if modified:
        value = re.sub(r'^\s*,\s*', '', value)
        if not value.strip():
            value = 'defaults'
    return value, modified


def process_fstab_for_encryption(fstab_path: str | Path) -> EncryptionPatchResult:
    path = Path(fstab_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    raw_content = path.read_bytes()
    try:
        content = raw_content.decode('utf-8')
        encoding = 'utf-8'
    except UnicodeDecodeError:
        content = raw_content.decode('latin-1')
        encoding = 'latin-1'

    pattern = re.compile(r'^(?P<fields>\S+\s+\S+\s+\S+)\s+(?P<options>.*)$')
    output_lines: list[str] = []
    modified_lines = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            output_lines.append(line)
            continue
        match = pattern.match(stripped)
        if match is None:
            output_lines.append(line)
            continue
        options, modified = clean_encryption_flags_preserve_format(match.group('options'))
        if modified:
            modified_lines += 1
            output_lines.append(f"{match.group('fields')} {options}")
        else:
            output_lines.append(line)

    if modified_lines:
        new_content = '\n'.join(output_lines)
        if not new_content.endswith('\n'):
            new_content += '\n'
        path.write_bytes(new_content.encode(encoding))
    return EncryptionPatchResult(path=path, modified=bool(modified_lines), encoding=encoding, modified_lines=modified_lines)


__all__ = [
    'ENCRYPTION_FLAGS_TO_REMOVE_BY_PREFIX',
    'ENCRYPTION_FLAGS_TO_REMOVE_EXACT',
    'EncryptionPatchResult',
    'clean_encryption_flags_preserve_format',
    'process_fstab_for_encryption',
]
