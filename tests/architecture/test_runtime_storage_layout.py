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



from tests.support.paths import PROJECT_ROOT
def test_root_config_contains_only_editable_application_configuration() -> None:
    actual = {
        path.relative_to(PROJECT_ROOT / "config").as_posix()
        for path in (PROJECT_ROOT / "config").rglob("*")
        if path.is_file()
    }
    assert actual == {
        "context_rules.json",
        "mtk_port_profiles.json",
        "settings.ini",
    }


def test_plugins_have_one_database_and_separate_install_directory() -> None:
    assert (PROJECT_ROOT / "plugins" / "plugin_db.json").is_file()
    assert (PROJECT_ROOT / "plugins" / "installed").is_dir()
    assert not (PROJECT_ROOT / "cache" / "plugin_catalog.json").exists()
    assert not (PROJECT_ROOT / "data" / "plugin_catalog.json").exists()
    assert not (PROJECT_ROOT / "bin" / "plugin_db.json").exists()
    assert not (PROJECT_ROOT / "bin" / "module").exists()


def test_runtime_temporary_directories_live_outside_bin() -> None:
    required = (
        "temp/plugins/downloads",
        "temp/plugins/runtime",
        "temp/updates",
        "temp/magisk",
        "temp/mtk_port",
    )
    assert all((PROJECT_ROOT / relative).is_dir() for relative in required)
    assert not (PROJECT_ROOT / "bin" / "temp").exists()


def test_ota_files_are_templates_not_application_settings() -> None:
    template_dir = PROJECT_ROOT / "templates" / "ota"
    assert {
        path.name for path in template_dir.iterdir() if path.is_file()
    } == {
        "ab_partitions.txt",
        "dynamic_partitions_info.txt",
        "misc_info.txt",
        "postinstall_config.txt",
    }
    assert not (PROJECT_ROOT / "config" / "ota").exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
