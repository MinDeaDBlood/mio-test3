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
from zipfile import ZipFile

from src.app.bug_report.controller import (
    BugReportApplicationContext,
    BugReportController,
)
from src.app.bug_report_runtime import snapshot_settings
from src.logic.bug_report.service.service import BugReportRequest, generate_bug_report


def test_generate_bug_report_writes_real_zip_from_explicit_request(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "tool.log"
    log_file.write_text("real log content\n", encoding="utf-8")
    output_dir = tmp_path / "reports"
    output_dir.mkdir()

    result = Path(
        generate_bug_report(
            BugReportRequest(
                output_dir=str(output_dir),
                tool_log=str(log_file),
                version_code="fixed-code",
                tool_version="4.1.7",
                run_source="source-build",
                settings={"theme": "dark", "language": "Russian"},
            )
        )
    )

    assert result.parent == output_dir
    assert result.name.endswith("_fixed-code.zip")
    with ZipFile(result) as archive:
        assert set(archive.namelist()) == {"detail.txt", "tool.log"}
        assert archive.read("tool.log").decode("utf-8").splitlines() == [
            "real log content"
        ]
        details = archive.read("detail.txt").decode("utf-8")
    assert "Tool Version: 4.1.7" in details
    assert "Source code running: source-build" in details
    assert "\tlanguage=Russian" in details
    assert "\ttheme=dark" in details


def test_bug_report_controller_owns_selection_and_worker_orchestration(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "tool.log"
    log_file.write_text("log", encoding="utf-8")
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    completed: list[str] = []
    workers: list[object] = []

    def start_worker(worker):
        workers.append(worker)
        return worker()

    controller = BugReportController(
        context=BugReportApplicationContext(
            tool_log=str(log_file),
            version_code="controller-code",
            tool_version="4.1.7",
            run_source="tests",
            settings={"language": "Russian"},
        ),
        choose_output=lambda: str(output_dir),
        start_worker=start_worker,
    )

    result = controller.request_generation(completed.append)

    assert len(workers) == 1
    assert isinstance(result, str)
    assert completed == [result]
    assert Path(result).is_file()


def test_bug_report_controller_does_not_start_worker_without_output_directory() -> None:
    called = False

    def start_worker(_worker):
        nonlocal called
        called = True

    controller = BugReportController(
        context=BugReportApplicationContext(
            tool_log="unused.log",
            version_code="unused",
            tool_version="unused",
            run_source="unused",
            settings={},
        ),
        choose_output=lambda: None,
        start_worker=start_worker,
    )

    assert controller.request_generation() is None
    assert called is False


def test_snapshot_settings_copies_only_public_scalar_values() -> None:
    class Settings:
        def __init__(self) -> None:
            self.language = "Russian"
            self.alpha = 0.9
            self.enabled = True
            self.optional = None
            self.config = object()
            self.mapping = {"not": "a scalar"}
            self._private = "hidden"

    assert snapshot_settings(Settings()) == {
        "alpha": "0.9",
        "enabled": "True",
        "language": "Russian",
        "optional": "",
    }

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
