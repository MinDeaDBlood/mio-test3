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
import os
import shutil
import signal
import select
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import BinaryIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]


TEST_TIMEOUT_SECONDS = 300
PREFLIGHT_TESTS = {
    "test_integrity",
    "required_assets",
    "required_dependencies_smoke",
    "localization_keys",
    "metric_baselines",
    "runtime_contracts",
}

DISPLAY_TESTS = {
    "welcome_smoke",
    "ui_smoke",
    "settings_ui_smoke",
    "theme_cycle_smoke",
    "window_smoke",
    "window_catalog_smoke",
    "byte_calculator_smoke",
    "toolbox_click_smoke",
    "runtime_smoke",
    "scenario_smoke",
    "operational_smoke",
    "e2e_flow_smoke",
    "lifecycle_smoke",
    "deep_happy_path_smoke",
    "metric_collection",
}

TESTS = [
    (
        "test_integrity",
        [sys.executable, "scripts/quality/check_test_integrity.py"],
    ),
    (
        "required_assets",
        [sys.executable, "scripts/quality/check_required_assets.py"],
    ),
    (
        "required_dependencies_smoke",
        [
            sys.executable,
            "scripts/quality/check_required_dependencies.py",
            "--smoke-only",
        ],
    ),
    (
        "localization_keys",
        [
            sys.executable,
            "scripts/quality/check_localization_keys.py",
            "--max-warning-issues",
            "15",
            "--max-missing-keys-per-language",
            "165",
        ],
    ),
    (
        "metric_baselines",
        [sys.executable, "scripts/quality/check_metric_baselines.py"],
    ),
    (
        "runtime_contracts",
        [sys.executable, "scripts/quality/check_runtime_contracts.py"],
    ),
    ("targeted", [sys.executable, "tests/smoke/targeted.py"]),
    ("welcome_smoke", [sys.executable, "tests/smoke/welcome.py"]),
    ("ui_smoke", [sys.executable, "tests/smoke/ui.py"]),
    ("settings_ui_smoke", [sys.executable, "tests/smoke/settings_ui.py"]),
    ("theme_cycle_smoke", [sys.executable, "tests/smoke/theme_cycle.py"]),
    ("window_smoke", [sys.executable, "tests/smoke/windows.py"]),
    (
        "window_catalog_smoke",
        [sys.executable, "tests/smoke/window_catalog.py"],
    ),
    ("byte_calculator_smoke", [sys.executable, "tests/smoke/byte_calculator.py"]),
    ("toolbox_click_smoke", [sys.executable, "tests/smoke/toolbox_click.py"]),
    ("runtime_smoke", [sys.executable, "tests/smoke/runtime.py"]),
    ("scenario_smoke", [sys.executable, "tests/smoke/scenario.py"]),
    ("operational_smoke", [sys.executable, "tests/smoke/operational.py"]),
    ("e2e_flow_smoke", [sys.executable, "tests/e2e/main_flow.py"]),
    ("lifecycle_smoke", [sys.executable, "tests/smoke/lifecycle.py"]),
    ("deep_happy_path_smoke", [sys.executable, "tests/smoke/deep_happy_path.py"]),
    (
        "metric_collection",
        [sys.executable, "scripts/quality/collect_metric_observations.py"],
    ),
    (
        "metric_observations",
        [sys.executable, "scripts/quality/check_metric_observations.py"],
    ),
]


def _start_xvfb_environment(
    base_env: dict[str, str],
) -> tuple[subprocess.Popen[bytes] | None, dict[str, str], BinaryIO | None]:
    """Return the native desktop environment or start one isolated Xvfb server."""
    if os.name == "nt" or sys.platform == "darwin":
        return None, base_env, None

    xvfb = shutil.which("Xvfb")
    if xvfb is None:
        if base_env.get("DISPLAY"):
            return None, base_env, None
        raise RuntimeError("runtime GUI smoke requires DISPLAY or Xvfb")

    read_fd, write_fd = os.pipe()
    error_log = tempfile.TemporaryFile(mode="w+b")
    process = subprocess.Popen(
        [
            xvfb,
            "-displayfd",
            str(write_fd),
            "-screen",
            "0",
            "1280x1024x24",
            "-nolisten",
            "tcp",
        ],
        pass_fds=(write_fd,),
        stdout=subprocess.DEVNULL,
        stderr=error_log,
        start_new_session=True,
    )
    os.close(write_fd)
    try:
        ready, _, _ = select.select([read_fd], [], [], 10)
        if not ready:
            raise RuntimeError(
                "Xvfb did not publish a display number within 10 seconds"
            )
        display_number = os.read(read_fd, 64).decode("ascii", errors="strict").strip()
        if not display_number:
            raise RuntimeError("Xvfb returned an empty display number")
        if process.poll() is not None:
            raise RuntimeError(
                f"Xvfb exited before the GUI test started with code {process.returncode}"
            )
    except Exception:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        error_log.seek(0)
        details = error_log.read().decode("utf-8", errors="replace").strip()
        error_log.close()
        if details:
            raise RuntimeError(details)
        raise
    finally:
        os.close(read_fd)

    env = base_env.copy()
    env["DISPLAY"] = f":{display_number}"
    return process, env, error_log


def _stop_xvfb(
    process: subprocess.Popen[bytes] | None,
    error_log: BinaryIO | None,
) -> None:
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
    if error_log is not None:
        error_log.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the complete explicit runtime smoke suite.')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='validate and print the configured commands without launching them',
    )
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    options = parser.parse_args(arguments)
    if options.dry_run:
        missing: list[str] = []
        for label, cmd in TESTS:
            print("==> " + label + ": " + " ".join(cmd), flush=True)
            for argument in cmd[1:]:
                if not argument.endswith('.py'):
                    continue
                candidate = PROJECT_ROOT / argument
                if not candidate.is_file():
                    missing.append(f'{label}: {argument}')
        if missing:
            for item in missing:
                print(f'MISSING: {item}', flush=True)
            return 1
        print('RUNTIME_SMOKE_SUITE_DRY_RUN_OK', flush=True)
        return 0
    from src.platform.metrics_repository import reset_metric_observations_file

    failures: list[str] = []
    metrics_file = Path(tempfile.gettempdir()) / "mio_runtime_metric_observations.jsonl"
    os.environ["MIO_METRIC_OBSERVATIONS_FILE"] = str(metrics_file)
    reset_metric_observations_file()

    base_env = os.environ.copy()
    display_env = base_env
    display_ready = False
    xvfb_process: subprocess.Popen[bytes] | None = None
    xvfb_error_log: BinaryIO | None = None

    try:
        for label, cmd in TESTS:
            print("==> " + label + ": " + " ".join(cmd), flush=True)
            try:
                if label in DISPLAY_TESTS and not display_ready:
                    xvfb_process, display_env, xvfb_error_log = _start_xvfb_environment(
                        base_env
                    )
                    display_ready = True
                env = display_env if label in DISPLAY_TESTS else base_env
                proc = subprocess.Popen(
                    cmd,
                    cwd=PROJECT_ROOT,
                    env=env,
                    start_new_session=True,
                )
                try:
                    returncode = proc.wait(timeout=TEST_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        proc.wait()
                    print(
                        f"TIMEOUT: {label} exceeded {TEST_TIMEOUT_SECONDS}s",
                        flush=True,
                    )
                    failures.append(label)
                    continue
            except RuntimeError as exc:
                print(f"ERROR: {label}: {exc}", flush=True)
                returncode = 1
            if returncode != 0:
                failures.append(label)
                if label in PREFLIGHT_TESTS:
                    print(
                        f"ABORTED: preflight check failed before runtime smoke: {label}",
                        flush=True,
                    )
                    break
    finally:
        _stop_xvfb(xvfb_process, xvfb_error_log)

    if failures:
        print(f"FAILED: {', '.join(failures)}", flush=True)
        return 1
    print("RUNTIME_SMOKE_SUITE_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
