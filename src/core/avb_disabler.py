from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

AVB_FLAGS_TO_REMOVE_BY_PREFIX: tuple[str, ...] = ('avb=', 'avb_keys=')
AVB_FLAGS_TO_REMOVE_EXACT: set[str] = {'avb', 'verify'}


@dataclass(frozen=True)
class AvbPatchResult:
    path: Path
    modified: bool
    encoding: str
    modified_lines: int


def clean_avb_flags(options_part: str) -> tuple[str, bool]:
    modified_options = options_part
    was_modified = False
    for prefix in AVB_FLAGS_TO_REMOVE_BY_PREFIX:
        pattern = rf'(?i)(,\s*|\s+){re.escape(prefix)}[^\s,]*'
        if re.search(pattern, modified_options):
            was_modified = True
            modified_options = re.sub(pattern, '', modified_options)
    for flag in AVB_FLAGS_TO_REMOVE_EXACT:
        pattern = rf'(?i)(,\s*|\s+)\b{re.escape(flag)}\b'
        if re.search(pattern, modified_options):
            was_modified = True
            modified_options = re.sub(pattern, '', modified_options)
    if was_modified:
        modified_options = re.sub(r'^\s*,\s*', '', modified_options)
        if not modified_options.strip():
            return 'defaults', True
    return modified_options, was_modified


def process_fstab(fstab_path: str | Path) -> AvbPatchResult:
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
        options, modified = clean_avb_flags(match.group('options'))
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
    return AvbPatchResult(path=path, modified=bool(modified_lines), encoding=encoding, modified_lines=modified_lines)


__all__ = ['AVB_FLAGS_TO_REMOVE_BY_PREFIX', 'AVB_FLAGS_TO_REMOVE_EXACT', 'AvbPatchResult', 'clean_avb_flags', 'process_fstab']
