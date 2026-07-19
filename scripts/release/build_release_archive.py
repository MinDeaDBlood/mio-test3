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
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.release.release_manifest import (
    DEFAULT_MANIFEST_PATH,
    build_manifest,
    dumps_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE_ROOT = PROJECT_ROOT / "dist"
DEFAULT_OUTPUT = PROJECT_ROOT.parent / f"{PROJECT_ROOT.name}-release.zip"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".vscode",
    "__pycache__",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}
REPOSITORY_ONLY_TOP_LEVEL_DIRS = {
    ".github",
    "audit",
    "docs",
    "readmes",
    "scripts",
    "src",
    "tests",
}
REPOSITORY_ONLY_TOP_LEVEL_FILES = {
    ".gitignore",
    "README.md",
    "build.py",
    "requirements-quality.txt",
    "requirements.txt",
    "ruff.toml",
    "tool.py",
}
GENERATED_RUNTIME_DIRS = {
    Path("logs"),
    Path("plugins/installed"),
    Path("temp/magisk"),
    Path("temp/mtk_port"),
    Path("temp/plugins/downloads"),
    Path("temp/plugins/runtime"),
    Path("temp/updates"),
}
EXCLUDED_RUNTIME_DIRS = {
    Path("Projects"),
    Path("logs"),
    Path("plugins/installed"),
    Path("scripts/bin/temp"),
    Path("temp"),
}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _is_excluded(path: Path, *, package_root: Path, output: Path) -> bool:
    relative = path.relative_to(package_root)
    if any(part in EXCLUDED_DIR_NAMES for part in relative.parts):
        return True
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return True
    if path.resolve() == output.resolve():
        return True
    if relative.parts:
        top_level = relative.parts[0]
        if top_level in REPOSITORY_ONLY_TOP_LEVEL_DIRS:
            return True
        if len(relative.parts) == 1 and top_level in REPOSITORY_ONLY_TOP_LEVEL_FILES:
            return True
    return any(
        relative == directory or _is_relative_to(relative, directory)
        for directory in EXCLUDED_RUNTIME_DIRS
    )


def _iter_archive_files(*, package_root: Path, output: Path) -> list[Path]:
    files = [
        path
        for path in package_root.rglob("*")
        if path.is_file()
        and not _is_excluded(path, package_root=package_root, output=output)
    ]
    return sorted(files, key=lambda item: item.relative_to(package_root).as_posix())


def _run_check(cmd: list[str]) -> None:
    print("==> " + " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def _run_preflight_checks() -> None:
    _run_check([sys.executable, "scripts/quality/check_required_assets.py"])
    _run_check([sys.executable, "scripts/quality/check_typed_boundaries.py"])
    _run_check(
        [
            sys.executable,
            "scripts/quality/check_required_dependencies.py",
            "--smoke-only",
        ]
    )
    _run_check(
        [
            sys.executable,
            "scripts/quality/check_localization_keys.py",
            "--max-warning-issues",
            "15",
            "--max-missing-keys-per-language",
            "165",
        ]
    )
    _run_check([sys.executable, "scripts/arch_guard/main.py", "--quick"])


def build_archive(
    output: Path,
    *,
    run_checks: bool,
    include_manifest: bool = True,
    project_root: Path = DEFAULT_PACKAGE_ROOT,
    metadata_root: Path | None = None,
) -> Path:
    """Package runtime files from ``project_root`` into a user archive.

    The ``project_root`` name is retained for compatibility with existing callers.
    It represents the directory being packaged, normally ``dist``.
    """

    package_root = project_root.resolve()
    if not package_root.is_dir():
        raise NotADirectoryError(f"Runtime package root does not exist: {package_root}")

    resolved_metadata_root = (
        metadata_root.resolve()
        if metadata_root is not None
        else PROJECT_ROOT.resolve()
        if package_root == DEFAULT_PACKAGE_ROOT.resolve()
        else package_root
    )

    if run_checks:
        if resolved_metadata_root != PROJECT_ROOT.resolve():
            raise ValueError(
                "Preflight checks can only run against the application project root"
            )
        _run_preflight_checks()

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    archive_files = _iter_archive_files(package_root=package_root, output=output)
    if include_manifest:
        archive_files = [
            path
            for path in archive_files
            if path.relative_to(package_root).as_posix() != DEFAULT_MANIFEST_PATH
        ]

    written_names: set[str] = set()

    def write_file(archive: zipfile.ZipFile, file_path: Path) -> None:
        name = file_path.relative_to(package_root).as_posix()
        if name not in written_names:
            archive.write(file_path, name)
            written_names.add(name)

    def write_directory_placeholder(archive: zipfile.ZipFile, relative: Path) -> None:
        name = relative.as_posix().rstrip("/") + "/"
        if name not in written_names:
            archive.writestr(name, "")
            written_names.add(name)

    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
    ) as archive:
        for file_path in archive_files:
            write_file(archive, file_path)
        if include_manifest:
            manifest = build_manifest(
                project_root=resolved_metadata_root,
                archive_root=package_root,
                archive_files=archive_files,
                checks_run=run_checks,
                manifest_path=DEFAULT_MANIFEST_PATH,
            )
            archive.writestr(DEFAULT_MANIFEST_PATH, dumps_manifest(manifest))
            written_names.add(DEFAULT_MANIFEST_PATH)
        for relative in GENERATED_RUNTIME_DIRS:
            write_directory_placeholder(archive, relative)

    print(f"RELEASE_ARCHIVE_OK: {output}")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a user archive from dist and exclude repository only content."
        )
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Output ZIP path."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_PACKAGE_ROOT,
        help="Runtime package root. Defaults to dist.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Create the archive without running manual preflight checks.",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="Do not include release_manifest.json in the archive.",
    )
    args = parser.parse_args(argv)
    build_archive(
        args.output,
        run_checks=not args.skip_checks,
        include_manifest=not args.no_manifest,
        project_root=args.root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
