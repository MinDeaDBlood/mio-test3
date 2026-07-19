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
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    Path("icon.ico"),
    Path("splash.png"),
    Path("splash_loongarch.png"),
    Path("config/settings.ini"),
    Path("config/mtk_port_profiles.json"),
    Path("config/context_rules.json"),
    Path("templates/ota/postinstall_config.txt"),
    Path("templates/ota/ab_partitions.txt"),
    Path("templates/ota/dynamic_partitions_info.txt"),
    Path("templates/ota/misc_info.txt"),
    Path("plugins/plugin_db.json"),
    Path("languages/English.json"),
    Path("bin/Android/aarch64/imgkit"),
    Path("bin/Darwin/arm64/imgkit"),
    Path("bin/Linux/aarch64/imgkit"),
    Path("bin/Linux/x86_64/imgkit"),
    Path("bin/Windows/AMD64/imgkit.exe"),
)

OPTIONAL_UI_FILES = (Path("bin/kemiaojiang.png"),)

REQUIRED_DIRS = (
    Path("logs"),
    Path("config"),
    Path("templates/ota"),
    Path("languages"),
    Path("plugins/installed"),
    Path("temp/plugins/downloads"),
    Path("temp/plugins/runtime"),
    Path("temp/updates"),
    Path("temp/magisk"),
    Path("temp/mtk_port"),
    Path("bin/licenses"),
)


def _missing(paths: tuple[Path, ...]) -> list[str]:
    return [str(path) for path in paths if not (PROJECT_ROOT / path).exists()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate required repository and runtime assets.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    missing_files = _missing(REQUIRED_FILES)
    missing_dirs = _missing(REQUIRED_DIRS)
    missing_optional_ui = _missing(OPTIONAL_UI_FILES)

    if missing_files or missing_dirs:
        if missing_files:
            print(
                "Missing required files: " + ", ".join(missing_files), file=sys.stderr
            )
        if missing_dirs:
            print(
                "Missing required directories: " + ", ".join(missing_dirs),
                file=sys.stderr,
            )
        return 1

    if missing_optional_ui:
        print(
            "Missing optional UI assets: " + ", ".join(missing_optional_ui),
            file=sys.stderr,
        )
        print(
            "The welcome image is optional by design. Add the original file when that visual element is required.",
            file=sys.stderr,
        )

    print("REQUIRED_ASSETS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
