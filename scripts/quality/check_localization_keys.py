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
import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_LANGUAGE_DIR = Path("languages")
DEFAULT_REFERENCE_LANGUAGE = "English"
DEFAULT_REQUIRED_LANGUAGES = ("English",)

# A compact and stable release smoke contract. The full validation contract is
# discovered dynamically from current UI and app source code.
REQUIRED_RUNTIME_KEYS = (
    "main_window_composition_home",
    "main_window_composition_project",
    "main_window_composition_settings",
    "main_window_composition_about",
    "main_window_composition_tasks",
    "tools_view_title",
    "settings_builders_language_select_label",
    "startup_status_startup_duration_format",
    "update_presenter_update_download_failed",
    "update_presenter_new_version_format",
    "update_presenter_latest_version",
)

# The active localization contract is discovered from current UI and app code.
# Opaque migration keys are invalid in the finalized language catalog.
_RESOLVER_METHODS = {
    "resolve",
    "resolve_optional",
    "resolve_ui_text",
    "resolve_required_ui_text",
}
_CATALOG_METHODS = _RESOLVER_METHODS | {
    "current_language",
    "current_language_file",
}


@dataclass(frozen=True)
class LanguageIssue:
    language: str
    file: str
    kind: str
    keys: list[str]


@dataclass(frozen=True)
class LocalizationReport:
    root: str
    language_dir: str
    reference_language: str
    languages: list[str]
    required_languages: list[str]
    required_keys: list[str]
    missing_files: list[str]
    parse_errors: list[str]
    non_mapping_files: list[str]
    missing_required_keys: list[LanguageIssue]
    invalid_required_values: list[LanguageIssue]
    missing_reference_keys: list[LanguageIssue]
    invalid_values: list[LanguageIssue]

    @property
    def warnings(self) -> list[LanguageIssue]:
        return [*self.missing_reference_keys, *self.invalid_values]

    @property
    def blocking_issues(self) -> list[Any]:
        return [
            *self.missing_files,
            *self.parse_errors,
            *self.non_mapping_files,
            *self.missing_required_keys,
            *self.invalid_required_values,
        ]


def _module_path(root: Path, module_name: str) -> Path | None:
    candidate = root.joinpath(*module_name.split(".")).with_suffix(".py")
    return candidate if candidate.exists() else None


def _string_constants(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    constants: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            constants[node.targets[0].id] = node.value.value
    return constants


def _imported_key_modules(root: Path, tree: ast.Module) -> dict[str, dict[str, str]]:
    modules: dict[str, dict[str, str]] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            for imported in node.names:
                candidates: tuple[str, ...] = ()
                if imported.name == "keys":
                    candidates = (f"{module_name}.keys",)
                elif imported.name.endswith("_keys"):
                    candidates = (f"{module_name}.{imported.name}",)
                for candidate in candidates:
                    module_path = _module_path(root, candidate)
                    if module_path is not None:
                        modules[imported.asname or imported.name] = _string_constants(
                            module_path
                        )
        elif isinstance(node, ast.Import):
            for imported in node.names:
                if not (
                    imported.name.endswith(".keys") or imported.name.endswith("_keys")
                ):
                    continue
                module_path = _module_path(root, imported.name)
                if module_path is not None:
                    modules[imported.asname or imported.name.rsplit(".", 1)[-1]] = (
                        _string_constants(module_path)
                    )
    return modules


def _is_catalog_attribute(node: ast.Attribute) -> bool:
    value = node.value
    if isinstance(value, ast.Name) and value.id in {"texts", "language", "lang"}:
        return True
    return (
        isinstance(value, ast.Attribute)
        and isinstance(value.value, ast.Name)
        and value.value.id in {"self", "view"}
        and value.attr in {"_texts", "texts", "_language", "language", "lang"}
    )


def discover_active_localization_keys(root: Path) -> tuple[str, ...]:
    keys: set[str] = set()
    for source_root in (root / "src" / "ui", root / "src" / "app"):
        for source_path in sorted(source_root.rglob("*.py")):
            tree = ast.parse(
                source_path.read_text(encoding="utf-8"), filename=str(source_path)
            )
            key_modules = _imported_key_modules(root, tree)
            for node in ast.walk(tree):
                if (
                    source_root.name == "ui"
                    and isinstance(node, ast.Attribute)
                    and _is_catalog_attribute(node)
                    and node.attr not in _CATALOG_METHODS
                ):
                    keys.add(node.attr)
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _RESOLVER_METHODS
                    and node.args
                ):
                    continue
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(
                    first_arg.value, str
                ):
                    keys.add(first_arg.value)
                elif (
                    isinstance(first_arg, ast.Attribute)
                    and isinstance(first_arg.value, ast.Name)
                    and first_arg.value.id in key_modules
                ):
                    key_value = key_modules[first_arg.value.id].get(first_arg.attr)
                    if key_value:
                        keys.add(key_value)
    return tuple(sorted(keys))


def _is_valid_translation(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() != "none"
    )


def _language_file_name(language_name: str) -> str:
    return f"{language_name}.json"


def _load_language_maps(
    language_dir: Path,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    maps: dict[str, dict[str, Any]] = {}
    parse_errors: list[str] = []
    non_mapping_files: list[str] = []
    for path in sorted(language_dir.glob("*.json")):
        language = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            parse_errors.append(f"{path}: {exc}")
            continue
        if not isinstance(data, dict):
            non_mapping_files.append(str(path))
            continue
        maps[language] = data
    return maps, parse_errors, non_mapping_files


def _is_legacy_key(key: str) -> bool:
    return (key.startswith("text") and key[4:].isdigit()) or (
        key.startswith("t") and key[1:].isdigit()
    )


def _has_resolved_translation(data: dict[str, Any], key: str) -> bool:
    return _is_valid_translation(data.get(key))


def _missing_keys(data: dict[str, Any], keys: tuple[str, ...] | list[str]) -> list[str]:
    return [key for key in keys if not _has_resolved_translation(data, key)]


def _missing_direct_keys(
    data: dict[str, Any], keys: tuple[str, ...] | list[str]
) -> list[str]:
    return [key for key in keys if not _is_valid_translation(data.get(key))]


def _invalid_keys(
    data: dict[str, Any], keys: tuple[str, ...] | list[str] | None = None
) -> list[str]:
    selected_keys = list(keys) if keys is not None else sorted(data)
    return [
        key
        for key in selected_keys
        if key in data
        and (_is_legacy_key(key) or not _has_resolved_translation(data, key))
    ]


def build_report(
    *,
    root: Path,
    language_dir: Path,
    reference_language: str,
    required_languages: tuple[str, ...],
    required_keys: tuple[str, ...],
) -> LocalizationReport:
    maps, parse_errors, non_mapping_files = _load_language_maps(language_dir)
    missing_files = [
        str(language_dir / _language_file_name(language))
        for language in (*required_languages, reference_language)
        if language not in maps
    ]

    reference_map = maps.get(reference_language, {})
    reference_keys = sorted(reference_map)

    missing_required: list[LanguageIssue] = []
    invalid_required: list[LanguageIssue] = []
    missing_reference: list[LanguageIssue] = []
    invalid_values: list[LanguageIssue] = []

    for language in sorted(maps):
        data = maps[language]
        path = str(language_dir / _language_file_name(language))
        invalid_all = _invalid_keys(data)
        if invalid_all:
            invalid_values.append(
                LanguageIssue(language, path, "invalid_values", invalid_all)
            )
        if language in required_languages:
            missing = _missing_direct_keys(data, required_keys)
            invalid = _invalid_keys(data, required_keys)
            if missing:
                missing_required.append(
                    LanguageIssue(language, path, "missing_required_keys", missing)
                )
            if invalid:
                invalid_required.append(
                    LanguageIssue(language, path, "invalid_required_values", invalid)
                )
        if language != reference_language and reference_keys:
            missing = _missing_keys(data, reference_keys)
            if missing:
                missing_reference.append(
                    LanguageIssue(language, path, "missing_reference_keys", missing)
                )

    return LocalizationReport(
        root=str(root),
        language_dir=str(language_dir),
        reference_language=reference_language,
        languages=sorted(maps),
        required_languages=list(required_languages),
        required_keys=list(required_keys),
        missing_files=missing_files,
        parse_errors=parse_errors,
        non_mapping_files=non_mapping_files,
        missing_required_keys=missing_required,
        invalid_required_values=invalid_required,
        missing_reference_keys=missing_reference,
        invalid_values=invalid_values,
    )


def _print_issue_group(
    title: str, issues: list[LanguageIssue], *, limit: int = 12
) -> None:
    if not issues:
        return
    print(title)
    for issue in issues[:limit]:
        preview = ", ".join(issue.keys[:12])
        if len(issue.keys) > 12:
            preview += f", ... (+{len(issue.keys) - 12})"
        print(f"  - {issue.language}: {preview}")
    if len(issues) > limit:
        print(f"  ... (+{len(issues) - limit} language files)")


def _print_text_report(report: LocalizationReport, *, strict: bool) -> None:
    print(f"Localization directory: {report.language_dir}")
    print(f"Reference language: {report.reference_language}")
    print(f"Languages: {len(report.languages)} ({', '.join(report.languages)})")
    if report.missing_files:
        print("Missing required language files:")
        for item in report.missing_files:
            print(f"  - {item}")
    if report.parse_errors:
        print("Language JSON parse errors:")
        for item in report.parse_errors:
            print(f"  - {item}")
    if report.non_mapping_files:
        print("Language JSON files that are not mappings:")
        for item in report.non_mapping_files:
            print(f"  - {item}")
    _print_issue_group("Missing required runtime keys:", report.missing_required_keys)
    _print_issue_group(
        "Invalid required runtime values:", report.invalid_required_values
    )
    _print_issue_group("Invalid translation values:", report.invalid_values)
    _print_issue_group(
        "Legacy/reference keys not present in every language (non-blocking):",
        report.missing_reference_keys,
    )
    if strict:
        print("Strict mode: reference-key and invalid-value warnings are blocking.")


def _budget_violations(
    report: LocalizationReport,
    *,
    max_warning_issues: int | None,
    max_missing_keys_per_language: int | None,
) -> list[str]:
    violations: list[str] = []
    warning_count = len(report.warnings)
    if max_warning_issues is not None and warning_count > max_warning_issues:
        violations.append(
            f"warning issue count {warning_count} exceeds budget {max_warning_issues}"
        )
    if max_missing_keys_per_language is not None:
        for issue in report.missing_reference_keys:
            missing_count = len(issue.keys)
            if missing_count > max_missing_keys_per_language:
                violations.append(
                    f"{issue.language} has {missing_count} missing reference keys; "
                    f"budget is {max_missing_keys_per_language}"
                )
    return violations


def _as_json(
    report: LocalizationReport,
    *,
    strict: bool,
    max_warning_issues: int | None,
    max_missing_keys_per_language: int | None,
) -> str:
    payload = asdict(report)
    budget_violations = _budget_violations(
        report,
        max_warning_issues=max_warning_issues,
        max_missing_keys_per_language=max_missing_keys_per_language,
    )
    payload["strict"] = strict
    payload["blocking_issue_count"] = len(report.blocking_issues)
    payload["warning_issue_count"] = len(report.warnings)
    payload["warning_budget"] = {
        "max_warning_issues": max_warning_issues,
        "max_missing_keys_per_language": max_missing_keys_per_language,
        "violations": budget_violations,
        "violation_count": len(budget_violations),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate language maps used by release and smoke tests."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root. Defaults to this checkout.",
    )
    parser.add_argument(
        "--language-dir",
        type=Path,
        default=None,
        help="Language directory. Defaults to <root>/languages.",
    )
    parser.add_argument(
        "--reference",
        default=DEFAULT_REFERENCE_LANGUAGE,
        help="Reference language file stem.",
    )
    parser.add_argument(
        "--required-language",
        action="append",
        dest="required_languages",
        help="Required language file stem. Can be passed multiple times.",
    )
    parser.add_argument(
        "--required-key",
        action="append",
        dest="required_keys",
        help="Required runtime key. Can be passed multiple times.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on all missing reference keys and invalid translation values.",
    )
    parser.add_argument(
        "--max-warning-issues",
        type=int,
        default=None,
        help="Fail when the number of warning issue groups exceeds this budget.",
    )
    parser.add_argument(
        "--max-missing-keys-per-language",
        type=int,
        default=None,
        help="Fail when any language is missing more reference keys than this budget.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = args.root.resolve()
    language_dir = (args.language_dir or (root / DEFAULT_LANGUAGE_DIR)).resolve()
    required_languages = tuple(
        args.required_languages or DEFAULT_REQUIRED_LANGUAGES
    )
    required_keys = tuple(args.required_keys or discover_active_localization_keys(root))
    report = build_report(
        root=root,
        language_dir=language_dir,
        reference_language=args.reference,
        required_languages=required_languages,
        required_keys=required_keys,
    )
    budget_violations = _budget_violations(
        report,
        max_warning_issues=args.max_warning_issues,
        max_missing_keys_per_language=args.max_missing_keys_per_language,
    )
    if args.json:
        print(
            _as_json(
                report,
                strict=args.strict,
                max_warning_issues=args.max_warning_issues,
                max_missing_keys_per_language=args.max_missing_keys_per_language,
            )
        )
    else:
        _print_text_report(report, strict=args.strict)
        if (
            args.max_warning_issues is not None
            or args.max_missing_keys_per_language is not None
        ):
            print("Warning budget:")
            print(f"  max warning issues: {args.max_warning_issues}")
            print(
                f"  max missing keys per language: {args.max_missing_keys_per_language}"
            )
        if budget_violations:
            print("Localization warning budget violations:")
            for violation in budget_violations:
                print(f"  - {violation}")

    failed = bool(report.blocking_issues)
    if args.strict:
        failed = failed or bool(report.warnings)
    if budget_violations:
        failed = True
    if failed:
        return 1
    if not args.json:
        print("LOCALIZATION_KEYS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
