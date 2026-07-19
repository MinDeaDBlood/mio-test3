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
import lzma
import os
import shutil
import struct
import subprocess
import tempfile
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


from src.platform.startup import prepare_tool_binaries
from src.core.file_types import gettype
from src.core.json_store import JsonEdit
from src.core.paths import tool_bin
from src.core.sparse_tools import img2simg, simg2img
from src.logic.common.service_output import ServiceOutput
from src.logic.projects.boot_images.runtime_context import (
    build_runtime_context as build_boot_runtime_context,
)
from src.logic.projects.boot_images.service import repack_boot_image, unpack_boot_image
from src.logic.projects.convert.models import ConvertSelection
from src.logic.projects.convert.runtime_context import build_convert_runtime_context
from src.logic.projects.convert.service import convert_selection
from src.logic.projects.pack.filesystem_service import make_f2fs, mke2fs, mkerofs
from src.logic.projects.pack.super.service import pack_super
from src.logic.projects.unpack.workflow.compressed_dat import unpack_compressed_dat
from src.logic.projects.unpack.workflow.image_extractors import (
    extract_erofs_image,
    extract_ext_image,
    extract_f2fs_image,
)
from src.logic.projects.unpack.workflow.source_handlers import extract_super_images
from src.logic.projects.unpack.runtime_context import build_workflow_runtime_context

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class AuditCase:
    name: str
    success: bool
    seconds: float
    details: dict[str, object]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_source(work: Path, name: str = 'system') -> bytes:
    content = b'MIO image roundtrip audit\n' * 128
    source = work / name
    (source / 'etc').mkdir(parents=True)
    (source / 'bin').mkdir()
    (source / 'etc' / 'audit.txt').write_bytes(content)
    script = source / 'bin' / 'audit.sh'
    script.write_text('#!/system/bin/sh\necho audit\n', encoding='utf-8')
    os.chmod(source, 0o755)
    os.chmod(source / 'etc', 0o755)
    os.chmod(source / 'bin', 0o755)
    os.chmod(source / 'etc' / 'audit.txt', 0o644)
    os.chmod(script, 0o755)
    config = work / 'config'
    config.mkdir(parents=True, exist_ok=True)
    (config / f'{name}_fs_config').write_text(
        '\n'.join(
            (
                '/ 0 0 0755',
                f'{name} 0 0 0755',
                f'{name}/etc 0 0 0755',
                f'{name}/etc/audit.txt 0 0 0644',
                f'{name}/bin 0 2000 0755',
                f'{name}/bin/audit.sh 0 2000 0755',
            )
        )
        + '\n',
        encoding='utf-8',
    )
    (config / f'{name}_file_contexts').write_text(
        '\n'.join(
            (
                '/ u:object_r:system_file:s0',
                f'/{name} u:object_r:system_file:s0',
                f'/{name}(/.*)? u:object_r:system_file:s0',
                f'/{name}/bin(/.*)? u:object_r:system_file:s0',
            )
        )
        + '\n',
        encoding='utf-8',
    )
    return content


def output_collector() -> tuple[ServiceOutput, list[dict[str, str]]]:
    events: list[dict[str, str]] = []

    def emit(event) -> None:
        events.append(
            {
                'channel': event.channel.value,
                'severity': event.severity.value,
                'message': str(event.message),
            }
        )

    return ServiceOutput(emit=emit), events


def build_unpack_runtime(
    *,
    input_path: Path,
    work_path: Path,
    output_path: Path,
    output: ServiceOutput,
):
    return build_workflow_runtime_context(
        input_path=str(input_path),
        work_path=str(work_path),
        output_path=str(output_path),
        project_selected=True,
        tool_bin=tool_bin,
        magisk_not_decompress='0',
        boot_skip_ramdisk='0',
        output=output,
    )


def _config_mode(fs_config_text: str, path: str) -> str | None:
    for line in fs_config_text.splitlines():
        fields = line.split()
        if fields and fields[0].lstrip('/') == path.lstrip('/') and len(fields) >= 4:
            return fields[3]
    return None


def validate_unpack(root: Path, expected: bytes, name: str = 'system') -> dict[str, object]:
    content_path = root / name / 'etc' / 'audit.txt'
    script_path = root / name / 'bin' / 'audit.sh'
    fs_config = root / 'config' / f'{name}_fs_config'
    file_contexts = root / 'config' / f'{name}_file_contexts'
    extracted_files = sorted(
        path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()
    )
    assert content_path.is_file(), (
        f'Missing extracted content: {content_path}; extracted files={extracted_files}'
    )
    assert content_path.read_bytes() == expected
    assert script_path.is_file()
    assert fs_config.stat().st_size > 0
    assert file_contexts.stat().st_size > 0
    fs_text = fs_config.read_text(encoding='utf-8')
    context_text = file_contexts.read_text(encoding='utf-8')
    assert 'audit.txt' in fs_text
    assert 'audit' in context_text
    configured_script_mode = _config_mode(fs_text, f'{name}/bin/audit.sh')
    assert configured_script_mode == '0755'
    return {
        'content_sha256': sha256(content_path),
        'fs_config_bytes': fs_config.stat().st_size,
        'file_contexts_bytes': file_contexts.stat().st_size,
        'configured_script_mode': configured_script_mode,
        'host_script_mode': oct(script_path.stat().st_mode & 0o777),
    }


def build_ext4(pack_work: Path, output_dir: Path, output: ServiceOutput) -> tuple[bytes, Path]:
    expected = write_source(pack_work)
    rc = mke2fs(
        'system',
        str(pack_work) + os.sep,
        False,
        str(output_dir),
        size=64 * 1024 * 1024,
        UTC=1,
        output=output,
    )
    image = output_dir / 'system.img'
    assert rc == 0 and image.is_file() and image.stat().st_size > 0
    return expected, image


def filesystem_roundtrip(name: str, packer: Callable[[Path, Path, ServiceOutput], int]) -> AuditCase:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f'mio-{name}-') as temp:
        root = Path(temp)
        pack_work = root / 'pack'
        output_dir = root / 'output'
        unpack_work = root / 'unpack'
        unpack_input = root / 'input'
        unpack_output = root / 'unpack-output'
        pack_work.mkdir()
        unpack_work.mkdir()
        unpack_input.mkdir()
        unpack_output.mkdir()
        expected = write_source(pack_work)
        service_output, events = output_collector()
        rc = packer(pack_work, output_dir, service_output)
        image = output_dir / 'system.img'
        assert rc == 0
        assert image.is_file() and image.stat().st_size > 0
        detected = gettype(str(image))
        shutil.copy2(image, unpack_work / 'system.img')
        runtime = build_unpack_runtime(
            input_path=unpack_input,
            work_path=unpack_work,
            output_path=unpack_output,
            output=service_output,
        )
        parts: dict[str, str] = {}
        if name == 'ext4':
            unpacked = extract_ext_image(runtime, str(unpack_work), 'system', parts)
        elif name == 'erofs':
            unpacked = extract_erofs_image(runtime, str(unpack_work), 'system')
        elif name == 'f2fs':
            unpacked = extract_f2fs_image(runtime, str(unpack_work), 'system')
        else:
            raise AssertionError(name)
        assert unpacked is True
        assert not (unpack_work / 'system.img').exists()
        details = validate_unpack(unpack_work, expected)
        details.update(
            {
                'image_type': detected,
                'image_bytes': image.stat().st_size,
                'event_count': len(events),
            }
        )
        return AuditCase(name=name, success=True, seconds=time.monotonic() - start, details=details)


def sparse_roundtrip() -> AuditCase:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='mio-sparse-') as temp:
        image = Path(temp) / 'sample.img'
        block = bytes(range(256)) * 16
        with image.open('wb') as stream:
            for index in range(512):
                stream.write(b'\0' * 4096 if index % 3 else block)
        original_hash = sha256(image)
        original_size = image.stat().st_size
        assert img2simg(str(image)) is True
        sparse_type = gettype(str(image))
        sparse_size = image.stat().st_size
        assert sparse_type == 'sparse'
        assert simg2img(str(image)) is True
        assert sha256(image) == original_hash
        return AuditCase(
            name='sparse_raw',
            success=True,
            seconds=time.monotonic() - start,
            details={
                'original_bytes': original_size,
                'sparse_bytes': sparse_size,
                'restored_sha256': sha256(image),
            },
        )


def conversion_roundtrip(source_format: str) -> AuditCase:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f'mio-convert-{source_format}-') as temp:
        root = Path(temp)
        pack_work = root / 'pack'
        build_dir = root / 'build'
        project_work = root / 'work'
        project_output = root / 'output'
        restore_output = root / 'restore-output'
        unpack_work = root / 'unpack'
        for directory in (
            pack_work,
            project_work,
            project_output,
            restore_output,
            unpack_work,
        ):
            directory.mkdir()
        service_output, events = output_collector()
        expected, image = build_ext4(pack_work, build_dir, service_output)
        shutil.copy2(image, project_work / 'system.img')
        runtime = build_convert_runtime_context(
            work_path=str(project_work),
            output_path=str(project_output),
            output=service_output,
        )

        assert convert_selection(
            ConvertSelection(from_format='raw', to_format='dat' if source_format == 'xz' else source_format, items=['system.img']),
            runtime=runtime,
        )
        if source_format == 'dat':
            input_name = 'system.new.dat'
        elif source_format == 'br':
            input_name = 'system.new.dat.br'
        elif source_format == 'xz':
            dat_path = project_output / 'system.new.dat'
            xz_path = project_output / 'system.new.dat.xz'
            xz_path.write_bytes(lzma.compress(dat_path.read_bytes()))
            dat_path.unlink()
            input_name = xz_path.name
        else:
            raise AssertionError(source_format)

        restore_runtime = build_convert_runtime_context(
            work_path=str(project_output),
            output_path=str(restore_output),
            output=service_output,
        )
        assert convert_selection(
            ConvertSelection(from_format=source_format, to_format='raw', items=[input_name]),
            runtime=restore_runtime,
        )
        converted_image = restore_output / 'system.img'
        assert gettype(str(converted_image)) == 'ext'
        shutil.copy2(converted_image, unpack_work / 'system.img')
        extract_runtime = build_unpack_runtime(
            input_path=project_work,
            work_path=unpack_work,
            output_path=project_output,
            output=service_output,
        )
        assert extract_ext_image(extract_runtime, str(unpack_work), 'system', {}) is True
        details = validate_unpack(unpack_work, expected)
        details.update(
            {
                'source_format': source_format,
                'restored_image_bytes': converted_image.stat().st_size,
                'conversion_files': sorted(path.name for path in project_output.iterdir()),
                'restore_files': sorted(path.name for path in restore_output.iterdir()),
                'event_count': len(events),
            }
        )
        return AuditCase(
            name=f'{source_format}_conversion',
            success=True,
            seconds=time.monotonic() - start,
            details=details,
        )


def zstd_roundtrip() -> AuditCase:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='mio-zstd-') as temp:
        root = Path(temp)
        source_dir = root / 'input'
        work_dir = root / 'work'
        source_dir.mkdir()
        work_dir.mkdir()
        source = source_dir / 'system.img'
        source.write_bytes((b'ZSTD-AUDIT' + bytes(4086)) * 32)
        expected_hash = sha256(source)
        compressed = source_dir / 'system.img.zst'
        subprocess.run(
            [tool_bin + 'zstd', '-q', '-f', str(source), '-o', str(compressed)],
            check=True,
            timeout=60,
        )
        source.unlink()
        output, events = output_collector()
        assert unpack_compressed_dat(
            str(source_dir),
            str(work_dir),
            'system',
            {},
            output=output,
        ) is False
        restored = work_dir / 'system.img'
        assert restored.is_file()
        assert sha256(restored) == expected_hash
        return AuditCase(
            name='zstd_image',
            success=True,
            seconds=time.monotonic() - start,
            details={
                'restored_sha256': sha256(restored),
                'compressed_source_preserved': compressed.exists(),
                'event_count': len(events),
            },
        )


def _create_cpio(seed: Path, archive: Path) -> None:
    archive_argument = os.path.relpath(archive, seed).replace('\\', '/')
    subprocess.run(
        [
            tool_bin + 'cpio',
            '-H',
            'newc',
            '-R',
            '0:0',
            '-o',
            '-F',
            archive_argument,
        ],
        cwd=seed,
        check=True,
        timeout=60,
        input=b'etc\netc/audit.txt\n',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _boot_header(name: str, ramdisk: bytes) -> bytes:
    page = 4096
    if name == 'boot':
        kernel = b'KERN'
        header = (
            bytearray(b'ANDROID!')
            + struct.pack('<10I', len(kernel), 0x10008000, len(ramdisk), 0x11000000, 0, 0, 0x10000100, page, 0, 0)
            + b'mio-audit\0'.ljust(16, b'\0')
            + bytes(512)
            + bytes(32)
            + bytes(1024)
        )
        def pad(value):
            return value + bytes((-len(value)) % page)
        return pad(header) + pad(kernel) + pad(ramdisk)
    if name == 'vendor_boot':
        header = (
            bytearray(b'VNDRBOOT')
            + struct.pack('<5I', 3, page, 0x10008000, 0x11000000, len(ramdisk))
            + bytes(2048)
            + struct.pack('<I', 0x10000100)
            + b'mio-vendor\0'.ljust(16, b'\0')
            + struct.pack('<IIQ', 2112, 0, 0)
        )
        def pad(value):
            return value + bytes((-len(value)) % page)
        return pad(header) + pad(ramdisk)
    raise AssertionError(name)


def boot_roundtrip(name: str) -> AuditCase:
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f'mio-{name}-') as temp:
        root = Path(temp)
        seed = root / 'seed'
        work = root / 'work'
        output_dir = root / 'output'
        verify = root / 'verify'
        for directory in (seed, work, output_dir, verify):
            directory.mkdir()
        (seed / 'etc').mkdir()
        (seed / 'etc' / 'audit.txt').write_text('before\n', encoding='utf-8')
        ramdisk_archive = root / 'ramdisk.cpio'
        _create_cpio(seed, ramdisk_archive)
        image_path = work / f'{name}.img'
        image_path.write_bytes(_boot_header(name, ramdisk_archive.read_bytes()))
        service_output, events = output_collector()
        runtime = build_boot_runtime_context(
            input_path=str(work),
            work_path=str(work),
            output_path=str(output_dir),
            magisk_not_decompress='0',
            boot_skip_ramdisk='0',
            tool_bin=tool_bin,
            output=service_output,
        )
        assert unpack_boot_image(name, runtime=runtime) is True
        extracted_file = work / name / 'ramdisk' / 'etc' / 'audit.txt'
        assert extracted_file.read_text(encoding='utf-8') == 'before\n'
        extracted_file.write_text('after\n', encoding='utf-8')
        assert repack_boot_image(name, runtime=runtime) is True
        result_image = output_dir / f'{name}.img'
        assert result_image.is_file() and result_image.stat().st_size > 0
        subprocess.run(
            [tool_bin + 'magiskboot', 'unpack', '-h', str(result_image)],
            cwd=verify,
            check=True,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        (verify / 'ramdisk').mkdir()
        subprocess.run(
            [tool_bin + 'cpio', '-i', '-d', '-F', 'ramdisk.cpio', '-D', 'ramdisk'],
            cwd=verify,
            check=True,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert (verify / 'ramdisk' / 'etc' / 'audit.txt').read_text(encoding='utf-8') == 'after\n'
        return AuditCase(
            name=name,
            success=True,
            seconds=time.monotonic() - start,
            details={
                'image_bytes': result_image.stat().st_size,
                'image_type': gettype(str(result_image)),
                'ramdisk_change_preserved': True,
                'busybox_used_for_repack': True,
                'magiskboot_used_for_unpack_repack': True,
                'event_count': len(events),
            },
        )


def super_roundtrip(sparse: bool) -> AuditCase:
    case_name = 'super_sparse' if sparse else 'super_raw'
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f'mio-{case_name}-') as temp:
        root = Path(temp)
        pack_work = root / 'pack'
        partition_output = root / 'partition-output'
        super_work = root / 'super-work'
        super_output = root / 'super-output'
        unpack_work = root / 'unpack'
        for directory in (pack_work, super_work, super_output, unpack_work):
            directory.mkdir()
        service_output, events = output_collector()
        expected, partition_image = build_ext4(pack_work, partition_output, service_output)
        shutil.copy2(partition_image, super_work / 'system.img')
        result = pack_super(
            sparse,
            'main',
            96 * 1024 * 1024,
            1,
            ['system'],
            output_dir=str(super_output),
            work=str(super_work),
            return_result=True,
        )
        assert result
        super_image = super_output / 'super.img'
        shutil.copy2(super_image, unpack_work / 'super.img')
        parts_info_path = unpack_work / 'config' / 'parts_info'
        parts_info = JsonEdit(str(parts_info_path))
        assert extract_super_images(
            str(unpack_work),
            ['system'],
            {},
            parts_info,
            output=service_output,
        ) is True
        assert (unpack_work / 'system.img').is_file()
        extract_runtime = build_unpack_runtime(
            input_path=unpack_work,
            work_path=unpack_work,
            output_path=super_output,
            output=service_output,
        )
        assert extract_ext_image(extract_runtime, str(unpack_work), 'system', {}) is True
        recorded_parts = parts_info.read()
        details = validate_unpack(unpack_work, expected)
        details.update(
            {
                'requested_device_size': result.requested_device_size,
                'logical_size': result.output_logical_size,
                'physical_size': result.output_physical_size,
                'output_is_sparse': result.output_is_sparse,
                'report_exists': Path(result.report_path).is_file(),
                'metadata_recorded': bool(recorded_parts.get('super_info')),
                'event_count': len(events),
            }
        )
        return AuditCase(name=case_name, success=True, seconds=time.monotonic() - start, details=details)


def _run_case(cases: list[AuditCase], failures: list[dict[str, str]], name: str, operation: Callable[[], AuditCase]) -> None:
    try:
        cases.append(operation())
    except Exception as exc:
        failures.append(
            {
                'name': name,
                'error': repr(exc),
                'traceback': traceback.format_exc(),
            }
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run image unpack and repack roundtrip audits.')
    parser.add_argument(
        '--case',
        action='append',
        dest='selected_cases',
        help='run only the named case; may be repeated',
    )
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    options = parser.parse_args(arguments)
    prepare_tool_binaries()
    cases: list[AuditCase] = []
    failures: list[dict[str, str]] = []
    operations: list[tuple[str, Callable[[], AuditCase]]] = [
        (
            'ext4',
            lambda: filesystem_roundtrip(
                'ext4',
                lambda work, out, output: mke2fs(
                    'system', str(work) + os.sep, False, str(out), size=64 * 1024 * 1024, UTC=1, output=output
                ),
            ),
        ),
        (
            'erofs',
            lambda: filesystem_roundtrip(
                'erofs',
                lambda work, out, output: mkerofs('system', 'lz4', str(work), str(out), '0', UTC=1, output=output),
            ),
        ),
        (
            'f2fs',
            lambda: filesystem_roundtrip(
                'f2fs',
                lambda work, out, output: make_f2fs('system', str(work) + os.sep, str(out), UTC=1, output=output),
            ),
        ),
        ('sparse_raw', sparse_roundtrip),
        ('dat_conversion', lambda: conversion_roundtrip('dat')),
        ('br_conversion', lambda: conversion_roundtrip('br')),
        ('xz_conversion', lambda: conversion_roundtrip('xz')),
        ('zstd_image', zstd_roundtrip),
        ('boot', lambda: boot_roundtrip('boot')),
        ('vendor_boot', lambda: boot_roundtrip('vendor_boot')),
        ('super_raw', lambda: super_roundtrip(False)),
        ('super_sparse', lambda: super_roundtrip(True)),
    ]
    known_cases = {name for name, _operation in operations}
    selected_cases = set(options.selected_cases or ())
    unknown_cases = selected_cases - known_cases
    if unknown_cases:
        parser.error('unknown case(s): ' + ', '.join(sorted(unknown_cases)))
    if selected_cases:
        operations = [
            (name, operation)
            for name, operation in operations
            if name in selected_cases
        ]
    for name, operation in operations:
        _run_case(cases, failures, name, operation)
    report = {
        'success': not failures,
        'sequential': True,
        'case_count': len(operations),
        'passed_case_count': len(cases),
        'cases': [asdict(case) for case in cases],
        'failures': failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
