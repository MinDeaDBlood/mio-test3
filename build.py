#!/usr/bin/env python3
# Copyright (C) 2022-2026 The MIO-KITCHEN-SOURCE Project
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0.

from __future__ import annotations

import argparse
import configparser
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import zipfile
from typing import Optional

RELEASE_TARGETS = {'win', 'ubuntu24.04', 'macos15'}
PYINSTALLER_PATHS = ['.']
PYINSTALLER_HIDDEN_IMPORTS = [
    'tkinter',
    'PIL',
    'PIL._tkinter_finder',
    'requests',
    'zstandard',
    'google.protobuf',
]
PYINSTALLER_EXCLUDES = ['numpy']
ICON_PATH = Path('icon.ico')
STARTUP_SPLASH_PATH = Path('splash.png')
LOONGARCH_SPLASH_PATH = Path('splash_loongarch.png')
RUNTIME_DIRECTORIES = (
    'logs',
    'plugins/installed',
    'temp',
    'temp/plugins',
    'temp/plugins/downloads',
    'temp/plugins/runtime',
    'temp/updates',
    'temp/magisk',
    'temp/mtk_port',
)
COMMON_BIN_ENTRIES = (
    'licenses',
    'keys',
    'extra_flash',
    'kemiaojiang.png',
    'License_kemiaojiang.txt',
    'exec.sh',
    'update-binary',
)


def struct_calc_bits() -> int:
    import struct

    return struct.calcsize('P') * 8


def normalize_target_os(ostype: str, target_os: Optional[str]) -> Optional[str]:
    if target_os is None:
        if ostype == 'Windows':
            raise ValueError('Windows builds require --target-os win')
        return None

    normalized = target_os.lower()
    if normalized not in RELEASE_TARGETS:
        raise ValueError(f'Unsupported --target-os: {target_os}')
    expected_platform = {
        'win': 'Windows',
        'ubuntu24.04': 'Linux',
        'macos15': 'Darwin',
    }[normalized]
    if ostype != expected_platform:
        raise ValueError(
            f'Target {normalized} requires {expected_platform}, current platform is {ostype}'
        )
    return normalized


def resolve_artifact_name(
    ostype: str,
    machine: Optional[str] = None,
    bits: Optional[int] = None,
    target_os: Optional[str] = None,
) -> str:
    machine_name = (machine or platform.machine()).lower()
    normalized = normalize_target_os(ostype, target_os)

    if ostype == 'Windows':
        if (bits or struct_calc_bits()) != 64:
            raise ValueError('The Windows release target supports only 64-bit builds')
        return 'MIO-KITCHEN-win.x64.zip'
    if ostype == 'Linux':
        if normalized == 'ubuntu24.04':
            if machine_name not in {'x86_64', 'amd64'}:
                raise ValueError('The Ubuntu 24.04 release target requires x86_64')
            return 'MIO-KITCHEN-ubuntu24.04-x64.zip'
        if machine_name in {'aarch64', 'arm64'}:
            return 'MIO-KITCHEN-linux.arm64.zip'
        if machine_name == 'loongarch64':
            return 'MIO-KITCHEN-linux.loongarch64.zip'
        return 'MIO-KITCHEN-linux.x64.zip'
    if ostype == 'Darwin':
        if normalized == 'macos15':
            if machine_name in {'x86_64', 'amd64'}:
                return 'MIO-KITCHEN-macos15-intel-x64.zip'
            if machine_name in {'arm64', 'aarch64'}:
                return 'MIO-KITCHEN-macos15-arm64.zip'
            raise ValueError(f'Unsupported macOS 15 architecture: {machine_name}')
        return (
            'MIO-KITCHEN-macos.x64.zip'
            if machine_name in {'x86_64', 'amd64'}
            else 'MIO-KITCHEN-macos.arm64.zip'
        )
    raise ValueError(f'Unsupported platform: {ostype}')


def _startup_splash_path(ostype: str, machine: str) -> Path:
    if ostype == 'Linux' and machine.lower() == 'loongarch64':
        return LOONGARCH_SPLASH_PATH.resolve()
    return STARTUP_SPLASH_PATH.resolve()


def build_pyinstaller_args(ostype: str, machine: Optional[str] = None) -> list[str]:
    machine_name = machine or platform.machine()
    bundle_mode = '--onedir' if ostype == 'Darwin' else '--onefile'
    args = [
        'tool.py',
        bundle_mode,
        '--windowed',
        '--clean',
        '--noconfirm',
        '--specpath',
        'build',
        '--name',
        'tool',
        '--icon',
        str(ICON_PATH.resolve()),
        '--add-data',
        f'{_startup_splash_path(ostype, machine_name)}{os.pathsep}.',
        '--collect-data',
        'sv_ttk',
        '--collect-data',
        'chlorophyll',
        '--collect-submodules',
        'src',
    ]
    for path in PYINSTALLER_PATHS:
        args.extend(['--paths', path])
    for hidden_import in PYINSTALLER_HIDDEN_IMPORTS:
        args.extend(['--hidden-import', hidden_import])
    for excluded_module in PYINSTALLER_EXCLUDES:
        args.extend(['--exclude-module', excluded_module])
    return args


def _dnd_platform(ostype: str, machine: str) -> str:
    normalized = machine.lower()
    if ostype == 'Windows' and normalized in {'amd64', 'x86_64'}:
        return 'win-x64'
    if ostype == 'Linux' and normalized in {'amd64', 'x86_64'}:
        return 'linux-x64'
    if ostype == 'Linux' and normalized in {'aarch64', 'arm64'}:
        return 'linux-arm64'
    if ostype == 'Linux' and normalized == 'loongarch64':
        return 'linux-loongarch64'
    if ostype == 'Darwin' and normalized in {'amd64', 'x86_64'}:
        return 'osx-x64'
    if ostype == 'Darwin' and normalized in {'aarch64', 'arm64'}:
        return 'osx-arm64'
    raise ValueError(f'Unsupported TkDnD platform: {ostype} {machine}')


def _platform_binary_path(ostype: str, machine: str) -> Path:
    normalized = machine.lower()
    directory_name = machine
    if ostype == 'Windows' and normalized in {'amd64', 'x86_64'}:
        directory_name = 'AMD64'
    elif ostype == 'Linux' and normalized in {'amd64', 'x86_64'}:
        directory_name = 'x86_64'
    elif ostype == 'Darwin' and normalized in {'amd64', 'x86_64'}:
        directory_name = 'x86_64'
    elif normalized in {'aarch64', 'arm64'}:
        directory_name = 'arm64' if ostype == 'Darwin' else 'aarch64'
    return Path('bin') / ostype / directory_name


def _copy_entry(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True, copy_function=shutil.copy2)
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _add_execute_bits(path: Path) -> None:
    if not path.is_file():
        return
    current_mode = path.stat().st_mode
    path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _zip_directory_entry(archive: zipfile.ZipFile, relative_path: str) -> None:
    normalized = relative_path.replace(os.sep, '/').rstrip('/') + '/'
    info = zipfile.ZipInfo(normalized)
    info.create_system = 3
    info.external_attr = (stat.S_IFDIR | 0o755) << 16
    archive.writestr(info, b'')


class Builder:
    def __init__(
        self,
        target_os: Optional[str] = None,
        *,
        skip_install: bool = False,
        requirements_file: str = 'requirements.txt',
    ):
        self.ostype = platform.system()
        self.machine = platform.machine()
        self.target_os = normalize_target_os(self.ostype, target_os)
        self.name = resolve_artifact_name(
            self.ostype,
            self.machine,
            struct_calc_bits(),
            self.target_os,
        )
        self.local = Path.cwd()
        self.dndplat = _dnd_platform(self.ostype, self.machine)
        self.skip_install = skip_install
        self.requirements_file = requirements_file

    def build(self) -> None:
        print('Building...')
        self.validate_sources()
        if self.skip_install:
            print('Skipping dependency installation; using prepared environment.')
        else:
            self.install_package()
        self.clean_build_directories()
        self.pyinstaller_build()
        self.config_folder()
        release_root = self.release_root()
        self.validate_release_tree(release_root)
        self.pack_zip(release_root, self.name)

    def validate_sources(self) -> None:
        required = [
            Path('tool.py'),
            ICON_PATH,
            Path('config/settings.ini'),
            Path('plugins/plugin_db.json'),
            Path('languages/English.json'),
            Path('bin/tkdnd') / self.dndplat,
            _platform_binary_path(self.ostype, self.machine),
        ]
        required.append(_startup_splash_path(self.ostype, self.machine))
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError('Missing required build resources: ' + ', '.join(missing))

    def clean_build_directories(self) -> None:
        for directory in (self.local / 'build', self.local / 'dist'):
            shutil.rmtree(directory, ignore_errors=True)
        output = self.local / self.name
        if output.exists():
            output.unlink()

    def run_command(self, command: list[str], strip: bool = False) -> Optional[str]:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return result.stdout.strip() if strip else result.stdout

    def generate_release_body(self) -> None:
        print('Generating Release Body...')
        parser = configparser.ConfigParser()
        parser.read('config/settings.ini', encoding='utf-8')
        version = parser.get('setting', 'version', fallback='unknown')
        head = self.run_command(['git', 'rev-parse', 'HEAD'], strip=True) or 'unknown'
        changelog = (
            self.run_command(['git', 'log', '-1', '--pretty=%B', head], strip=True)
            or 'No changelog was provided.'
        )
        with open('body.md', 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(f'Build: {os.getenv("GITHUB_RUN_NUMBER", "local")}\n')
            stream.write(f'Actor: {os.getenv("GITHUB_TRIGGERING_ACTOR", "local")}\n')
            stream.write(f'Repository: {os.getenv("GITHUB_REPOSITORY", "local")}\n')
            stream.write(f'Version: {version}\n\n')
            stream.write('## Changelog\n\n')
            stream.write(changelog.rstrip() + '\n')

    def move_artifacts(self) -> None:
        for artifact in (
            'MIO-KITCHEN-win.x64',
            'MIO-KITCHEN-ubuntu24.04-x64',
            'MIO-KITCHEN-macos15-intel-x64',
            'MIO-KITCHEN-macos15-arm64',
        ):
            source = Path(artifact) / f'{artifact}.zip'
            if source.is_file():
                source.replace(Path(f'{artifact}.zip'))

    def install_package(self) -> None:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', self.requirements_file],
            check=True,
        )

    def pyinstaller_build(self) -> None:
        import PyInstaller.__main__

        PyInstaller.__main__.run(
            build_pyinstaller_args(self.ostype, self.machine)
        )

    def release_root(self) -> Path:
        return Path(self.local) / 'dist'

    def _executable_path(self, release_root: Path) -> Path:
        if self.ostype == 'Windows':
            return release_root / 'tool.exe'
        if self.ostype == 'Darwin':
            return release_root / 'tool.app' / 'Contents' / 'MacOS' / 'tool'
        return release_root / 'tool'

    def validate_release_tree(self, release_root: Path) -> None:
        executable = self._executable_path(release_root)
        missing: list[str] = []
        if not executable.is_file():
            missing.append(str(executable))
        for relative_dir in RUNTIME_DIRECTORIES:
            if not (release_root / relative_dir).is_dir():
                missing.append(str(release_root / relative_dir))

        platform_relative = _platform_binary_path(self.ostype, self.machine)
        source_platform = Path(self.local) / platform_relative
        destination_platform = release_root / platform_relative
        for source_file in source_platform.rglob('*'):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_platform)
            destination_file = destination_platform / relative
            if not destination_file.is_file():
                missing.append(str(destination_file))
            elif destination_file.stat().st_size != source_file.stat().st_size:
                raise RuntimeError(
                    f'Bundled tool size mismatch: {destination_file}'
                )

        dnd_path = release_root / 'bin' / 'tkdnd' / self.dndplat
        if not dnd_path.is_dir():
            missing.append(str(dnd_path))
        if missing:
            raise FileNotFoundError(
                'Incomplete release tree. Missing: ' + ', '.join(missing)
            )

        total_size = sum(
            path.stat().st_size
            for path in release_root.rglob('*')
            if path.is_file()
        )
        print(
            f'Release tree verified: {release_root} '
            f'({total_size / (1024 * 1024):.1f} MiB uncompressed)'
        )

    def config_folder(self) -> None:
        local_root = Path(self.local)
        machine = getattr(self, 'machine', platform.machine())
        dist = local_root / 'dist'
        dist.mkdir(parents=True, exist_ok=True)
        release_root = self.release_root()
        release_root.mkdir(parents=True, exist_ok=True)
        dist_bin = release_root / 'bin'
        dist_bin.mkdir(parents=True, exist_ok=True)

        for entry_name in COMMON_BIN_ENTRIES:
            _copy_entry(local_root / 'bin' / entry_name, dist_bin / entry_name)

        platform_source = local_root / _platform_binary_path(self.ostype, machine)
        platform_destination = release_root / _platform_binary_path(self.ostype, machine)
        _copy_entry(platform_source, platform_destination)

        dnd_source = local_root / 'bin' / 'tkdnd' / self.dndplat
        dnd_destination = release_root / 'bin' / 'tkdnd' / self.dndplat
        _copy_entry(dnd_source, dnd_destination)

        for resource_dir in ('config', 'languages', 'templates'):
            _copy_entry(local_root / resource_dir, release_root / resource_dir)

        plugin_database = local_root / 'plugins' / 'plugin_db.json'
        _copy_entry(plugin_database, release_root / 'plugins' / 'plugin_db.json')
        _copy_entry(local_root / 'LICENSE', release_root / 'LICENSE')

        for relative_dir in RUNTIME_DIRECTORIES:
            (release_root / relative_dir).mkdir(parents=True, exist_ok=True)

        if os.name == 'posix':
            for binary in platform_destination.rglob('*'):
                if binary.is_file():
                    _add_execute_bits(binary)
            _add_execute_bits(release_root / 'bin' / 'exec.sh')
            _add_execute_bits(self._executable_path(release_root))

    def pack_zip(self, source: str | os.PathLike[str], name: str) -> None:
        source_root = Path(source).resolve()
        zip_path = Path(self.local) / name
        if zip_path.exists():
            zip_path.unlink()

        if self.ostype == 'Darwin':
            subprocess.run(
                [
                    '/usr/bin/ditto',
                    '-c',
                    '-k',
                    '--sequesterRsrc',
                    '.',
                    str(zip_path),
                ],
                cwd=source_root,
                check=True,
            )
            print(f'Pack ZIP done: {zip_path} ({zip_path.stat().st_size / (1024 * 1024):.1f} MiB)')
            return

        with zipfile.ZipFile(
            zip_path,
            'w',
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            written_directories: set[str] = set()

            def add_directory(relative_path: Path) -> None:
                normalized = relative_path.as_posix().rstrip('/') + '/'
                if normalized in written_directories:
                    return
                _zip_directory_entry(archive, normalized)
                written_directories.add(normalized)

            for root, directories, files in os.walk(source_root):
                root_path = Path(root)
                relative_root = root_path.relative_to(source_root)
                if relative_root.parts:
                    add_directory(relative_root)
                for directory in sorted(directories):
                    add_directory(relative_root / directory)
                for file_name in sorted(files):
                    file_path = root_path / file_name
                    relative_file = file_path.relative_to(source_root)
                    archive.write(file_path, relative_file.as_posix())
        print(f'Pack ZIP done: {zip_path} ({zip_path.stat().st_size / (1024 * 1024):.1f} MiB)')


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build and package MIO Kitchen release artifacts.'
    )
    parser.add_argument(
        'command',
        nargs='?',
        default='build',
        choices=('build', 'grb', 'ma'),
    )
    parser.add_argument(
        '--target-os',
        default=os.getenv('MIO_BUILD_TARGET_OS'),
        choices=('win', 'ubuntu24.04', 'macos15'),
    )
    parser.add_argument('--skip-install', action='store_true')
    parser.add_argument('--requirements-file', default='requirements.txt')
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    builder = Builder(
        target_os=args.target_os,
        skip_install=args.skip_install,
        requirements_file=args.requirements_file,
    )
    if args.command == 'build':
        builder.build()
    elif args.command == 'grb':
        builder.generate_release_body()
    else:
        builder.move_artifacts()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
