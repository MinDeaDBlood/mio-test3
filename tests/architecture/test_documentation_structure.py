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


import re
import tkinter as tk
from pathlib import Path

from src.logic.projects.common.project_manager import (
    INPUT_DIR_NAME,
    OUTPUT_DIR_NAME,
    PROJECTS_ROOT_DIR_NAME,
    UNPACK_DIR_NAME,
    ProjectManager,
)
from src.logic.projects.common.runtime_context import (
    build_project_path_runtime_context,
)
from tests.support.paths import PROJECT_ROOT


DOCS_ROOT = PROJECT_ROOT / "docs"
ACTIVE_LANGUAGE_ROOTS = {
    "en": DOCS_ROOT / "en",
    "ru": DOCS_ROOT / "ru",
}
CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04ff]")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PYTHON_SCRIPT_PATTERN = re.compile(r"\bpython\s+([\w./-]+\.py)\b")
DOCUMENTED_SOURCE_PATTERN = re.compile(r"\b(src/[A-Za-z0-9_./-]+\.py)\b")


def _active_markdown_files(language: str) -> set[str]:
    root = ACTIVE_LANGUAGE_ROOTS[language]
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if path.is_file()
    }


def _active_document_text(language: str) -> str:
    root = ACTIVE_LANGUAGE_ROOTS[language]
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.md"))
        if path.is_file()
    )


def _normalized_pair_link_targets(lines: list[str]) -> list[str]:
    targets: list[str] = []
    for target in MARKDOWN_LINK_PATTERN.findall("\n".join(lines)):
        path = target.split("#", 1)[0]
        path = re.sub(
            r"architecture_map_(?:english|russian)\.md",
            "architecture_map_LANGUAGE.md",
            path,
        )
        path = re.sub(
            r"\.\./(?:en|ru)/README\.md",
            "../LANGUAGE/README.md",
            path,
        )
        targets.append(path)
    return sorted(targets)


def _markdown_heading_slugs(path: Path) -> set[str]:
    slugs: set[str] = set()
    occurrences: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if match is None:
            continue
        heading = match.group(1).replace("`", "").lower()
        base = re.sub(r"[^\w\- ]", "", heading)
        base = re.sub(r"\s+", "-", base.strip())
        index = occurrences.get(base, 0)
        occurrences[base] = index + 1
        slugs.add(base if index == 0 else f"{base}-{index}")
    return slugs


def test_english_and_russian_documentation_have_matching_structure() -> None:
    common = {
        "README.md",
        "architecture/architecture_overview.md",
        "architecture/architecture_status.md",
        "architecture/module_boundaries.md",
        "architecture/runtime_state.md",
        "architecture/typed_boundaries.md",
        "development/localization_and_ui_text.md",
        "development/logging_and_diagnostics.md",
        "development/plugin_development.md",
        "development/repository_structure.md",
        "development/runtime_environment.md",
        "development/tests_and_scripts.md",
        "development/third_party_components.md",
    }

    assert _active_markdown_files("en") == common | {
        "architecture/architecture_map_english.md"
    }
    assert _active_markdown_files("ru") == common | {
        "architecture/architecture_map_russian.md"
    }
    assert (DOCS_ROOT / "README.md").is_file()
    assert (DOCS_ROOT / "archive/README.md").is_file()


def test_language_pairs_preserve_the_full_document_structure() -> None:
    pairs = [("README.md", "README.md")]
    for relative in sorted(_active_markdown_files("en") - {"README.md"}):
        russian_relative = (
            "architecture/architecture_map_russian.md"
            if relative == "architecture/architecture_map_english.md"
            else relative
        )
        pairs.append((relative, russian_relative))

    for english_relative, russian_relative in pairs:
        english_lines = (
            ACTIVE_LANGUAGE_ROOTS["en"] / english_relative
        ).read_text(encoding="utf-8").splitlines()
        russian_lines = (
            ACTIVE_LANGUAGE_ROOTS["ru"] / russian_relative
        ).read_text(encoding="utf-8").splitlines()
        assert abs(len(english_lines) - len(russian_lines)) <= 5, english_relative
        assert sum(line.startswith("#") for line in english_lines) == sum(
            line.startswith("#") for line in russian_lines
        ), english_relative
        assert sum(line.startswith("|") for line in english_lines) == sum(
            line.startswith("|") for line in russian_lines
        ), english_relative
        assert sum(line.startswith("```") for line in english_lines) == sum(
            line.startswith("```") for line in russian_lines
        ), english_relative
        assert sum(bool(re.match(r"^\d+\. ", line)) for line in english_lines) == sum(
            bool(re.match(r"^\d+\. ", line)) for line in russian_lines
        ), english_relative
        assert sum(line.startswith("- ") for line in english_lines) == sum(
            line.startswith("- ") for line in russian_lines
        ), english_relative
        assert len(MARKDOWN_LINK_PATTERN.findall("\n".join(english_lines))) == len(
            MARKDOWN_LINK_PATTERN.findall("\n".join(russian_lines))
        ), english_relative
        assert _normalized_pair_link_targets(
            english_lines
        ) == _normalized_pair_link_targets(russian_lines), english_relative
        assert english_lines.count("```mermaid") == russian_lines.count(
            "```mermaid"
        ), english_relative


def test_complete_architecture_maps_are_not_replaced_by_summaries() -> None:
    maps = {
        "en": ACTIVE_LANGUAGE_ROOTS["en"]
        / "architecture/architecture_map_english.md",
        "ru": ACTIVE_LANGUAGE_ROOTS["ru"]
        / "architecture/architecture_map_russian.md",
    }
    minimum_bytes = {"en": 64_536, "ru": 76_992}
    for language, path in maps.items():
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert path.stat().st_size >= minimum_bytes[language]
        assert len(lines) >= 1_112
        assert sum(line.startswith("#") for line in lines) >= 50
        assert lines.count("```mermaid") >= 22
        assert text.count("```") == 2 * text.count("```mermaid")


def test_each_active_tree_uses_its_own_language() -> None:
    english = _active_document_text("en")
    russian = _active_document_text("ru")

    assert CYRILLIC_PATTERN.search(english) is None
    for document in ACTIVE_LANGUAGE_ROOTS["ru"].rglob("*.md"):
        assert CYRILLIC_PATTERN.search(document.read_text(encoding="utf-8")), document
    assert len(CYRILLIC_PATTERN.findall(russian)) > 100


def test_active_markdown_relative_links_point_to_existing_files() -> None:
    broken: list[str] = []
    documents = [DOCS_ROOT / "README.md", DOCS_ROOT / "archive/README.md"]
    for root in ACTIVE_LANGUAGE_ROOTS.values():
        documents.extend(sorted(root.rglob("*.md")))

    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK_PATTERN.findall(text):
            if "://" in target:
                continue
            relative_target, separator, anchor = target.partition("#")
            resolved = (
                document.resolve()
                if not relative_target
                else (document.parent / relative_target).resolve()
            )
            if not resolved.exists():
                broken.append(
                    f"{document.relative_to(PROJECT_ROOT).as_posix()} -> {target}"
                )
                continue
            if separator and resolved.suffix.lower() == ".md":
                if anchor not in _markdown_heading_slugs(resolved):
                    broken.append(
                        f"{document.relative_to(PROJECT_ROOT).as_posix()} "
                        f"-> missing heading #{anchor} in "
                        f"{resolved.relative_to(PROJECT_ROOT).as_posix()}"
                    )

    assert broken == []


def test_documented_python_script_commands_exist() -> None:
    missing: list[str] = []
    for root in ACTIVE_LANGUAGE_ROOTS.values():
        for document in root.rglob("*.md"):
            text = document.read_text(encoding="utf-8")
            for script_path in PYTHON_SCRIPT_PATTERN.findall(text):
                if not (PROJECT_ROOT / script_path).is_file():
                    missing.append(
                        f"{document.relative_to(PROJECT_ROOT).as_posix()} -> {script_path}"
                    )
    assert missing == []


def test_documented_source_files_exist() -> None:
    missing: list[str] = []
    for root in ACTIVE_LANGUAGE_ROOTS.values():
        for document in root.rglob("*.md"):
            text = document.read_text(encoding="utf-8")
            for source_path in DOCUMENTED_SOURCE_PATTERN.findall(text):
                if not (PROJECT_ROOT / source_path).is_file():
                    missing.append(
                        f"{document.relative_to(PROJECT_ROOT).as_posix()} -> {source_path}"
                    )
    assert missing == []


def test_localization_documentation_tracks_the_real_code_layout() -> None:
    runtime_session_keys = "src/app/runtime/keys.py"
    localization_key_files = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for pattern in ("keys.py", "*_keys.py")
        for path in (PROJECT_ROOT / "src").rglob(pattern)
        if path.relative_to(PROJECT_ROOT).as_posix() != runtime_session_keys
    }
    required_runtime_files = {
        "languages/English.json",
        "languages/Russian.json",
        "config/settings.ini",
        "src/platform/runtime_paths.py",
        "src/platform/language_repository.py",
        "src/app/localization.py",
        "src/app/localization_runtime.py",
        "src/app/localization_selection.py",
        "src/ui/localization.py",
        "src/ui/common/technical_choice_keys.py",
        "src/ui/common/technical_choices.py",
        "src/ui/common/service_output.py",
        runtime_session_keys,
    }

    assert localization_key_files
    for language, root in ACTIVE_LANGUAGE_ROOTS.items():
        document = root / "development/localization_and_ui_text.md"
        text = document.read_text(encoding="utf-8")
        missing = sorted(
            path
            for path in localization_key_files | required_runtime_files
            if path not in text
        )
        assert missing == [], f"{language}: undocumented localization files: {missing}"


def test_welcome_documentation_tracks_the_prebuilt_page_stack() -> None:
    source = (PROJECT_ROOT / "src/ui/welcome/wizard.py").read_text(
        encoding="utf-8"
    )
    for implementation_token in (
        "frame.grid(row=0, column=0, sticky='nsew')",
        "self.frame.tkraise()",
        "self._set_active_page_focusability",
        "reveal_window_after_layout",
        "snapshot_window_transition",
    ):
        assert implementation_token in source

    for language, root in ACTIVE_LANGUAGE_ROOTS.items():
        document = root / "development/localization_and_ui_text.md"
        text = document.read_text(encoding="utf-8")
        for documented_token in (
            "`ttk.Frame`",
            "`tkraise`",
            "`takefocus`",
            "`snapshot_window_transition`",
        ):
            assert documented_token in text, f"{language}: missing {documented_token}"


def test_documented_project_layout_matches_real_project_manager(tmp_path: Path) -> None:
    interpreter = tk.Tcl()
    current_project = tk.StringVar(
        master=interpreter,
        value="Documentation Contract",
    )
    runtime = build_project_path_runtime_context(
        workspace_path=str(tmp_path),
        current_project_name=current_project,
    )
    manager = ProjectManager(runtime)

    project_root = Path(manager.new(current_project.get()))
    expected_root = tmp_path / PROJECTS_ROOT_DIR_NAME / "Documentation_Contract"
    assert project_root == expected_root
    assert {
        path.name for path in expected_root.iterdir() if path.is_dir()
    } == {INPUT_DIR_NAME, UNPACK_DIR_NAME, OUTPUT_DIR_NAME}
    assert Path(manager.current_work_path()) == expected_root / UNPACK_DIR_NAME

    english = _active_document_text("en")
    russian = _active_document_text("ru")
    for directory in (INPUT_DIR_NAME, UNPACK_DIR_NAME, OUTPUT_DIR_NAME):
        assert f"{PROJECTS_ROOT_DIR_NAME}/<name>/{directory}" in english
        assert f"{PROJECTS_ROOT_DIR_NAME}/<имя>/{directory}" in russian


def test_active_documentation_does_not_reference_removed_layout() -> None:
    stale_paths = (
        "docs/architecture",
        "docs/development",
        "docs/audits",
        "docs/readmes",
        "src/config",
        "src/infrastructure",
    )
    for language in ACTIVE_LANGUAGE_ROOTS:
        text = _active_document_text(language)
        for stale_path in stale_paths[:4]:
            assert stale_path not in text
        # Removed source packages may be named only while explaining that they
        # must stay absent.
        assert text.count("src/config") <= 2
        assert text.count("src/infrastructure") <= 2


def test_windows_double_click_launchers_live_only_in_scripts() -> None:
    expected = {
        "install_quality_tools.cmd",
        "run_all_checks.cmd",
        "run_architecture_check.cmd",
        "run_gui_checks.cmd",
        "run_mypy.cmd",
        "run_release_checks.cmd",
        "run_ruff.cmd",
    }
    assert {path.name for path in (PROJECT_ROOT / "scripts").glob("*.cmd")} == expected
    assert not any((PROJECT_ROOT / "src").rglob("*.cmd"))

    for launcher_name in expected:
        text = (PROJECT_ROOT / "scripts" / launcher_name).read_text(
            encoding="utf-8"
        )
        assert "py -3.12" not in text
        assert "where python" in text
        assert 'set "PYTHON=python"' in text
        assert 'set "PYTHON=py -3"' in text


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
