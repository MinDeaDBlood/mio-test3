"""Build deterministic manifest payloads for user release archives."""

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


import hashlib
import json
import platform
import sys
from dataclasses import asdict
from importlib import metadata
from pathlib import Path
from typing import Iterable

from scripts.quality import check_localization_keys, check_required_dependencies

MANIFEST_SCHEMA_VERSION = 1
DEFAULT_MANIFEST_PATH = "release_manifest.json"
DEFAULT_PREFLIGHT_COMMANDS = (
    "python scripts/quality/check_required_assets.py",
    "python scripts/quality/check_typed_boundaries.py",
    "python scripts/quality/check_required_dependencies.py --smoke-only",
    "python scripts/quality/check_localization_keys.py",
    "python scripts/arch_guard/main.py --quick",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(archive_root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(archive_root).as_posix()
    return {
        "path": relative,
        "size": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _dependency_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in check_required_dependencies.DEPENDENCIES:
        version = None
        if spec.distribution:
            try:
                version = metadata.version(spec.distribution)
            except metadata.PackageNotFoundError:
                version = None
        rows.append(
            {
                "import_name": spec.import_name,
                "distribution": spec.distribution,
                "category": spec.category,
                "required": spec.required,
                "platforms": list(spec.platforms),
                "version": version,
                "note": spec.note,
            }
        )
    return rows



def _localization_report(project_root: Path) -> dict[str, object]:
    report = check_localization_keys.build_report(
        root=project_root,
        language_dir=project_root / check_localization_keys.DEFAULT_LANGUAGE_DIR,
        reference_language=check_localization_keys.DEFAULT_REFERENCE_LANGUAGE,
        required_languages=check_localization_keys.DEFAULT_REQUIRED_LANGUAGES,
        required_keys=check_localization_keys.REQUIRED_RUNTIME_KEYS,
    )
    payload = asdict(report)
    payload["blocking_issue_count"] = len(report.blocking_issues)
    payload["warning_issue_count"] = len(report.warnings)
    return payload


def build_manifest(
    *,
    project_root: Path,
    archive_files: Iterable[Path],
    checks_run: bool,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    archive_root: Path | None = None,
) -> dict[str, object]:
    """Return a deterministic manifest for files included in a user archive."""

    project_root = project_root.resolve()
    resolved_archive_root = (archive_root or project_root).resolve()
    file_records = [
        _file_record(resolved_archive_root, path.resolve())
        for path in sorted(
            archive_files,
            key=lambda item: item.relative_to(resolved_archive_root).as_posix(),
        )
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_path": manifest_path,
        "project_root_name": project_root.name,
        "checks_run": checks_run,
        "preflight_commands": list(DEFAULT_PREFLIGHT_COMMANDS),
        "environment": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "dependency_inventory": _dependency_inventory(),
        "localization_report": _localization_report(project_root),
        "archive": {
            "file_count": len(file_records),
            "total_size": sum(int(record["size"]) for record in file_records),
            "files": file_records,
        },
    }


def dumps_manifest(manifest: dict[str, object]) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
