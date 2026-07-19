#!/usr/bin/env python3
from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import time
from uuid import UUID
import zlib

from PIL import Image


from src.core.android_sparse import split_raw_image_to_sparse_parts  # noqa: E402
from src.core.file_types import gettype  # noqa: E402
from src.core.imgkit import unpack_image as imgkit_unpack_image  # noqa: E402
from src.core.merge_sparse import SparseMergeStatus, merge_sparse_segments  # noqa: E402
from src.core.splash_editor import process_splashimg, splash_repack  # noqa: E402
from src.logic.common.service_output import build_service_output  # noqa: E402
from src.logic.projects.pack.filesystem_service import make_f2fs  # noqa: E402
from src.logic.projects.unpack.gpt import extract_gpt_partitions  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _case(name: str, callback):
    started = time.perf_counter()
    try:
        details = callback()
        return {'name': name, 'success': True, 'seconds': time.perf_counter() - started, 'details': details}
    except Exception as exc:
        return {
            'name': name,
            'success': False,
            'seconds': time.perf_counter() - started,
            'error': f'{type(exc).__name__}: {exc}',
        }


def _build_gpt_image(path: Path) -> bytes:
    sector_size = 512
    total_sectors = 128
    entry_count = 128
    entry_size = 128
    first_sector = 40
    last_sector = 42
    payload = bytes((index * 29) % 251 for index in range((last_sector - first_sector + 1) * sector_size))
    image = bytearray(total_sectors * sector_size)
    entries = bytearray(entry_count * entry_size)
    name = 'system'.encode('utf-16-le').ljust(72, b'\x00')
    entries[:128] = struct.pack(
        '<16s16sQQQ72s',
        UUID('0fc63daf-8483-4772-8e79-3d69d8477de4').bytes_le,
        UUID('11111111-2222-3333-4444-555555555555').bytes_le,
        first_sector,
        last_sector,
        0,
        name,
    )
    entry_crc = zlib.crc32(entries) & 0xFFFFFFFF
    image[2 * sector_size:2 * sector_size + len(entries)] = entries
    header = bytearray(
        struct.pack(
            '<8sIIIIQQQQ16sQIII',
            b'EFI PART',
            0x00010000,
            92,
            0,
            0,
            1,
            total_sectors - 1,
            34,
            total_sectors - 34,
            UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee').bytes_le,
            2,
            entry_count,
            entry_size,
            entry_crc,
        )
    )
    struct.pack_into('<I', header, 16, zlib.crc32(header) & 0xFFFFFFFF)
    image[sector_size:sector_size + len(header)] = header
    image[first_sector * sector_size:(last_sector + 1) * sector_size] = payload
    path.write_bytes(image)
    return payload


def _audit_imgkit_assets() -> dict:
    paths = (
        Path('bin/Android/aarch64/imgkit'),
        Path('bin/Darwin/arm64/imgkit'),
        Path('bin/Linux/aarch64/imgkit'),
        Path('bin/Linux/x86_64/imgkit'),
        Path('bin/Windows/AMD64/imgkit.exe'),
    )
    resolved = [PROJECT_ROOT / path for path in paths]
    missing = [str(path) for path in paths if not (PROJECT_ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError('Missing imgkit assets: ' + ', '.join(missing))
    return {
        'files': [
            {'path': str(path), 'bytes': target.stat().st_size, 'sha256': _sha256(target)}
            for path, target in zip(paths, resolved, strict=True)
        ]
    }


def _audit_f2fs_imgkit(root: Path) -> dict:
    work = root / 'work'
    output = root / 'output'
    unpacked = root / 'unpacked'
    (work / 'system' / 'bin').mkdir(parents=True)
    (work / 'config').mkdir(parents=True)
    output.mkdir()
    unpacked.mkdir()
    source_file = work / 'system' / 'bin' / 'hello'
    source_file.write_bytes(b'imgkit-f2fs-roundtrip\n')
    (work / 'config' / 'system_fs_config').write_text(
        'system 0 0 0755\n'
        'system/bin 0 0 0755\n'
        'system/bin/hello 0 0 0755\n',
        encoding='utf-8',
    )
    (work / 'config' / 'system_file_contexts').write_text(
        '/system(/.*)? u:object_r:system_file:s0\n',
        encoding='utf-8',
    )
    events = []
    return_code = make_f2fs(
        'system',
        str(work) + os.sep,
        str(output),
        output=build_service_output(emit=events.append),
    )
    if return_code != 0:
        raise RuntimeError(f'make_f2fs failed with exit code {return_code}')
    image = output / 'system.img'
    fs_config = unpacked / 'config' / 'system_fs_config'
    contexts = unpacked / 'config' / 'system_file_contexts'
    imgkit_unpack_image(
        image,
        unpacked,
        fs_config_path=fs_config,
        file_contexts_path=contexts,
        log_level=0,
    )
    restored = unpacked / 'system' / 'bin' / 'hello'
    if restored.read_bytes() != source_file.read_bytes():
        raise RuntimeError('imgkit F2FS roundtrip changed file content')
    if not fs_config.is_file() or fs_config.stat().st_size == 0:
        raise RuntimeError('imgkit did not produce fs_config')
    if not contexts.is_file() or contexts.stat().st_size == 0:
        raise RuntimeError('imgkit did not produce file_contexts')
    return {
        'image_type': gettype(str(image)),
        'image_bytes': image.stat().st_size,
        'content_sha256': _sha256(restored),
        'fs_config_bytes': fs_config.stat().st_size,
        'file_contexts_bytes': contexts.stat().st_size,
        'event_count': len(events),
    }


def _audit_gpt(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    source = root / 'gpt.img'
    expected = _build_gpt_image(source)
    result = extract_gpt_partitions(source, root / 'gpt-out')
    if len(result.partitions) != 1:
        raise RuntimeError(f'Expected one GPT partition, received {len(result.partitions)}')
    extracted = result.partitions[0].output_path
    if extracted.read_bytes() != expected:
        raise RuntimeError('GPT extracted partition content does not match source sectors')
    return {
        'image_type': gettype(str(source)),
        'partition_name': extracted.name,
        'partition_bytes': extracted.stat().st_size,
        'partition_sha256': _sha256(extracted),
    }


def _audit_splash(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    source_dir = root / 'splash-source'
    source_dir.mkdir()
    image1 = Image.new('RGB', (16, 8), (20, 40, 60))
    image2 = Image.new('RGBA', (9, 7), (200, 100, 50, 255))
    image1.save(source_dir / 'splash1.png')
    image2.save(source_dir / 'splash2.png')
    output = splash_repack(source_dir, root / 'splash.img', nolimit=True)
    extracted = process_splashimg(output, root / 'splash-out' / 'splash.png')
    with Image.open(extracted[0]) as restored1, Image.open(extracted[1]) as restored2:
        if restored1.convert('RGB').tobytes() != image1.tobytes():
            raise RuntimeError('First splash image changed during roundtrip')
        if restored2.convert('RGB').tobytes() != image2.convert('RGB').tobytes():
            raise RuntimeError('Second splash image changed during roundtrip')
    return {
        'image_type': gettype(str(output)),
        'entry_count': len(extracted),
        'output_bytes': output.stat().st_size,
        'extracted_files': [path.name for path in extracted],
    }


def _audit_split_super(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    block_size = 4096
    raw = bytearray((index * 17) % 256 for index in range(block_size * 11))
    raw[4096:4100] = b'\x67\x44\x6c\x61'
    source = root / 'super.img'
    source.write_bytes(raw)
    split = split_raw_image_to_sparse_parts(
        source,
        root / 'parts',
        part_count=4,
        block_size=block_size,
    )
    merged = root / 'merged-super.img'
    result = merge_sparse_segments(
        source_directory=root / 'parts',
        output_path=merged,
        tool_bin_path=root / 'unused',
    )
    if result.status is not SparseMergeStatus.MERGED:
        raise RuntimeError(f'Unexpected merge status: {result.status}')
    if merged.read_bytes() != bytes(raw):
        raise RuntimeError('Split and merged super image is not byte identical')
    return {
        'source_type': gettype(str(source)),
        'part_count': len(split.output_paths),
        'source_sha256': _sha256(source),
        'merged_sha256': _sha256(merged),
        'byte_exact': True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=PROJECT_ROOT / 'audit' / 'old_project_migration_results.json')
    args = parser.parse_args()
    cases = [_case('imgkit_assets', _audit_imgkit_assets)]
    with tempfile.TemporaryDirectory(prefix='mio-legacy-migration-') as temporary:
        root = Path(temporary)
        cases.extend(
            [
                _case('f2fs_imgkit_roundtrip', lambda: _audit_f2fs_imgkit(root / 'f2fs')),
                _case('gpt_extract', lambda: _audit_gpt(root / 'gpt')),
                _case('splash_roundtrip', lambda: _audit_splash(root / 'splash')),
                _case('split_super_roundtrip', lambda: _audit_split_super(root / 'split')),
            ]
        )
    report = {
        'success': all(case['success'] for case in cases),
        'sequential': True,
        'case_count': len(cases),
        'cases': cases,
        'failures': [case['name'] for case in cases if not case['success']],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
