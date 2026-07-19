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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse
import locale
import os
import shutil
import subprocess
import sys
import tempfile
from typing import BinaryIO
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]
    timeout: int | None = None
    use_xvfb: bool = False
    env: dict[str, str] | None = None


def python_module(module: str, *args: str) -> list[str]:
    return [PYTHON, "-m", module, *args]


def python_script(script: str, *args: str) -> list[str]:
    return [PYTHON, script, *args]


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing them."
    )


def wrap_for_xvfb(command: list[str]) -> list[str]:
    xvfb = shutil.which("xvfb-run")
    if xvfb:
        return ["env", "-u", "DISPLAY", xvfb, "-a", *command]
    return command


def format_command(command: list[str]) -> str:
    return " ".join(command)


def _read_captured_output(output: BinaryIO) -> str:
    output.flush()
    output.seek(0)
    payload = output.read()
    encodings = ("utf-8", locale.getpreferredencoding(False))
    for encoding in dict.fromkeys(encodings):
        try:
            return payload.decode(encoding, errors="strict")
        except (LookupError, UnicodeDecodeError):
            continue
    return payload.decode("utf-8", errors="replace")


def run_steps(
    steps: list[Step], *, dry_run: bool = False, cwd: Path = PROJECT_ROOT
) -> int:
    for step in steps:
        command = wrap_for_xvfb(step.command) if step.use_xvfb else step.command
        print(f"==> {step.name}: {format_command(command)}", flush=True)
        if dry_run:
            continue
        env = os.environ.copy()
        if step.env:
            env.update(step.env)
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        with tempfile.TemporaryFile(mode="w+b") as output:
            try:
                subprocess.run(
                    command,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    close_fds=True,
                    timeout=step.timeout,
                    check=True,
                )
            except subprocess.TimeoutExpired:
                captured = _read_captured_output(output)
                if captured:
                    print(captured, end="" if captured.endswith("\n") else "\n", flush=True)
                print(f"TIMEOUT: {step.name} exceeded {step.timeout}s", flush=True)
                return 124
            except subprocess.CalledProcessError as exc:
                captured = _read_captured_output(output)
                if captured:
                    print(captured, end="" if captured.endswith("\n") else "\n", flush=True)
                print(f"FAILED: {step.name} exited with {exc.returncode}", flush=True)
                return exc.returncode
            captured = _read_captured_output(output)
            if captured:
                print(captured, end="" if captured.endswith("\n") else "\n", flush=True)
    return 0


if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
