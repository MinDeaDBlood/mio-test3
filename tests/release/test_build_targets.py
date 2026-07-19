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


from pathlib import Path
import pytest

import build


def test_release_targets_have_exact_artifact_names() -> None:
    assert (
        build.resolve_artifact_name("Windows", "AMD64", 64, "win")
        == "MIO-KITCHEN-win.x64.zip"
    )
    assert (
        build.resolve_artifact_name("Linux", "x86_64", 64, "ubuntu24.04")
        == "MIO-KITCHEN-ubuntu24.04-x64.zip"
    )
    assert (
        build.resolve_artifact_name("Darwin", "x86_64", 64, "macos15")
        == "MIO-KITCHEN-macos15-intel-x64.zip"
    )
    assert (
        build.resolve_artifact_name("Darwin", "arm64", 64, "macos15")
        == "MIO-KITCHEN-macos15-arm64.zip"
    )


def test_release_targets_reject_wrong_platform_or_architecture() -> None:
    with pytest.raises(ValueError, match="64-bit"):
        build.resolve_artifact_name("Windows", "x86", 32, "win")
    with pytest.raises(ValueError, match="x86_64"):
        build.resolve_artifact_name("Linux", "aarch64", 64, "ubuntu24.04")
    with pytest.raises(ValueError, match="requires Linux"):
        build.resolve_artifact_name("Windows", "AMD64", 64, "ubuntu24.04")

def test_windows_target_must_be_explicit() -> None:
    with pytest.raises(ValueError, match="--target-os"):
        build.resolve_artifact_name("Windows", "AMD64", 64, None)



def test_github_workflow_builds_only_requested_release_targets() -> None:
    workflow = Path(".github/workflows/build.yml").read_text(encoding="utf-8")

    for runner in ("windows-latest", "ubuntu-24.04", "macos-15-intel", "macos-15"):
        assert runner in workflow
    for artifact in (
        "MIO-KITCHEN-win.x64",
        "MIO-KITCHEN-ubuntu24.04-x64",
        "MIO-KITCHEN-macos15-intel-x64",
        "MIO-KITCHEN-macos15-arm64",
    ):
        assert artifact in workflow

    assert "requirements-quality.txt" not in workflow
    assert "requirements-win7.txt" not in workflow
    assert "win7" not in workflow
    assert "win11.x86" not in workflow
    assert "architecture: x86" not in workflow
    assert "pytest" not in workflow
    assert "ruff" not in workflow
    assert "mypy" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "publish_release:" in workflow
    assert "release create" in workflow
    assert "actions/download-artifact@v4" in workflow
    assert "merge-multiple: true" in workflow

def test_windows_pyinstaller_args_do_not_require_missing_spec_file() -> None:
    args = build.build_pyinstaller_args("Windows", "AMD64")
    assert args[0] == "tool.py"
    assert "tool.spec" not in args
    assert "--collect-data" in args
    assert "--collect-submodules" in args
    assert "src" in args
    assert "--paths" in args
    assert "requests" in args
    assert "zstandard" in args
    assert "google.protobuf" in args
    assert build.PYINSTALLER_EXCLUDES == ["numpy"]
    assert "--onefile" in args
    assert "--onedir" not in args
    assert "--add-data" in args
    assert "--splash" not in args


def test_splash_assets_live_in_repository_root() -> None:
    standard_splash = Path("splash.png")
    loongarch_splash = Path("splash_loongarch.png")

    assert standard_splash.is_file()
    assert loongarch_splash.is_file()
    assert not Path("assets/build").exists()
    assert build._startup_splash_path("Windows", "AMD64") == standard_splash.resolve()
    assert build._startup_splash_path("Linux", "loongarch64") == loongarch_splash.resolve()


def test_pyinstaller_paths_reference_existing_directories() -> None:
    assert build.PYINSTALLER_PATHS == ["."]
    assert all(Path(path).exists() for path in build.PYINSTALLER_PATHS)


def test_pyinstaller_paths_do_not_shadow_standard_library_platform_module() -> None:
    assert "src" not in build.PYINSTALLER_PATHS
    assert "src/core" not in build.PYINSTALLER_PATHS
    tool_source = Path("tool.py").read_text(encoding="utf-8")
    assert "import platform" not in tool_source
    assert "platform.system()" not in tool_source
    assert "sys.platform == 'darwin'" in tool_source


def test_application_icon_is_required_and_embedded() -> None:
    assert build.ICON_PATH == Path("icon.ico")
    assert build.ICON_PATH.is_file()
    args = build.build_pyinstaller_args("Windows", "AMD64")
    icon_index = args.index("--icon")
    assert args[icon_index + 1] == str(build.ICON_PATH.resolve())


def test_windows_and_linux_use_single_file_without_internal_directory() -> None:
    for ostype, machine in (("Windows", "AMD64"), ("Linux", "x86_64")):
        args = build.build_pyinstaller_args(ostype, machine)
        assert "--onefile" in args
        assert "--onedir" not in args

    builder = build.Builder.__new__(build.Builder)
    builder.local = Path("/release-root")
    builder.ostype = "Windows"
    assert builder.release_root() == Path("/release-root/dist")


def test_macos_uses_onedir_without_pyinstaller_splash() -> None:
    for machine in ("x86_64", "arm64"):
        args = build.build_pyinstaller_args("Darwin", machine)
        assert "--onedir" in args
        assert "--onefile" not in args
        assert "--windowed" in args
        assert "--splash" not in args


def test_pyinstaller_bundles_only_the_startup_splash_as_root_data() -> None:
    args = build.build_pyinstaller_args("Windows", "AMD64")
    data_entries = [
        args[index + 1]
        for index, value in enumerate(args[:-1])
        if value == "--add-data"
    ]

    assert data_entries == [
        f"{build._startup_splash_path('Windows', 'AMD64')}{build.os.pathsep}."
    ]
    assert not any("src/core" in entry for entry in data_entries)


def test_builder_has_no_test_execution_path() -> None:
    source = Path(build.__file__).read_text(encoding="utf-8")
    assert "src.tool_tester" not in source
    assert "pytest" not in source
    assert "unit_test(" not in source


def test_config_folder_copies_only_runtime_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for directory in (
        "bin/licenses",
        "config",
        "languages",
        "templates",
        "plugins",
        "docs",
        "readmes",
        "scripts",
        "src",
        "tests",
    ):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)

    (tmp_path / "bin/licenses/license.txt").write_text("license", encoding="utf-8")
    (tmp_path / "config/settings.ini").write_text("[setting]", encoding="utf-8")
    (tmp_path / "languages/English.json").write_text("{}", encoding="utf-8")
    (tmp_path / "templates/example.txt").write_text("template", encoding="utf-8")
    (tmp_path / "plugins/plugin_db.json").write_text("{}", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("license", encoding="utf-8")
    (tmp_path / "README.md").write_text("repository", encoding="utf-8")
    for directory in ("docs", "readmes", "scripts", "src", "tests"):
        (tmp_path / directory / "repository-only.txt").write_text(
            "repository", encoding="utf-8"
        )

    builder = build.Builder.__new__(build.Builder)
    builder.local = str(tmp_path)
    builder.ostype = "Linux"
    builder.machine = "aarch64"
    builder.dndplat = "linux-arm64"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(build.platform, "machine", lambda: "aarch64")
    builder.config_folder()

    dist = tmp_path / "dist"
    assert (dist / "bin/licenses/license.txt").is_file()
    assert (dist / "config/settings.ini").is_file()
    assert (dist / "languages/English.json").is_file()
    assert (dist / "templates/example.txt").is_file()
    assert (dist / "plugins/plugin_db.json").is_file()
    assert (dist / "LICENSE").is_file()
    assert (dist / "plugins/installed").is_dir()
    assert (dist / "logs").is_dir()
    assert (dist / "temp/plugins/downloads").is_dir()
    assert (dist / "temp/plugins/runtime").is_dir()
    assert (dist / "temp/updates").is_dir()
    assert (dist / "temp/magisk").is_dir()
    assert (dist / "temp/mtk_port").is_dir()
    for repository_only in ("docs", "readmes", "scripts", "src", "tests"):
        assert not (dist / repository_only).exists()
    assert not (dist / "README.md").exists()


def test_pack_zip_preserves_empty_runtime_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dist = tmp_path / "dist"
    for relative_path in (
        "logs",
        "temp/plugins/downloads",
        "temp/plugins/runtime",
        "temp/updates",
        "temp/magisk",
        "temp/mtk_port",
        "plugins/installed",
    ):
        (dist / relative_path).mkdir(parents=True, exist_ok=True)
    (dist / "tool").write_text("binary", encoding="utf-8")

    builder = build.Builder.__new__(build.Builder)
    builder.local = tmp_path
    builder.ostype = "Linux"
    monkeypatch.chdir(tmp_path)
    builder.pack_zip(dist, "runtime.zip")

    import zipfile

    with zipfile.ZipFile(tmp_path / "runtime.zip") as archive:
        names = set(archive.namelist())
    assert "logs/" in names
    assert "temp/plugins/downloads/" in names
    assert "temp/plugins/runtime/" in names
    assert "temp/updates/" in names
    assert "temp/magisk/" in names
    assert "temp/mtk_port/" in names
    assert "plugins/installed/" in names


if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
