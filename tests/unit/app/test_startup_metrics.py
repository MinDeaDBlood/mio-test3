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
from types import SimpleNamespace

import pytest


from src.app.startup_metrics import StartupMark, StartupTimeline


class _CapturingLogger:
    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[tuple[str, tuple[object, ...]]] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warning(self, message: str, *args: object) -> None:
        self.warnings.append((message, args))


def test_startup_timeline_excludes_user_wait_from_budgeted_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.app.startup_metrics as startup_metrics

    monkeypatch.setattr(
        startup_metrics,
        "metric_budget",
        lambda label: 8.0 if label == "startup.total" else None,
    )
    timeline = StartupTimeline(start_time=0.0)
    timeline.marks = [
        StartupMark("process_streams", 0.1),
        StartupMark("welcome_interaction", 21.9, excluded_from_total=True),
        StartupMark("build_gui", 22.2),
    ]

    assert timeline.elapsed_total() == pytest.approx(0.4)
    assert timeline.elapsed_wall_total() == pytest.approx(22.2)

    summary = timeline.summary()
    assert "welcome_interaction=21.800s[excluded]" in summary
    assert "total=0.400s/8.000s[within-budget]" in summary
    assert "wall_total=22.200s" in summary


def test_startup_timeline_records_budgeted_total_and_informational_wall_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.app.startup_metrics as startup_metrics

    recorded: list[tuple[str, float, float | None, bool | None]] = []

    def fake_record(
        label: str,
        elapsed: float,
        *,
        budget: float | None = None,
        within_budget: bool | None = None,
    ) -> None:
        recorded.append((label, elapsed, budget, within_budget))

    monkeypatch.setattr(
        startup_metrics,
        "metric_budget",
        lambda label: 8.0 if label == "startup.total" else None,
    )
    monkeypatch.setattr(startup_metrics, "record_metric_observation", fake_record)

    timeline = StartupTimeline(start_time=0.0)
    timeline.marks = [
        StartupMark("process_streams", 0.1),
        StartupMark("welcome_interaction", 21.9, excluded_from_total=True),
        StartupMark("build_gui", 22.2),
    ]

    logger = _CapturingLogger()
    timeline.log(logger=logger)

    assert ("startup.total", pytest.approx(0.4), 8.0, True) == recorded[0]
    assert ("startup.wall_total", pytest.approx(22.2), None, None) == recorded[1]
    assert logger.warnings == []


def test_startup_timeline_warning_reports_slowest_non_excluded_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.app.startup_metrics as startup_metrics

    monkeypatch.setattr(
        startup_metrics,
        "metric_budget",
        lambda label: 8.0 if label == "startup.total" else None,
    )
    monkeypatch.setattr(
        startup_metrics, "record_metric_observation", lambda *args, **kwargs: None
    )

    timeline = StartupTimeline(start_time=0.0)
    timeline.marks = [
        StartupMark("process_streams", 2.5),
        StartupMark("build_gui", 7.7),
        StartupMark("welcome_interaction", 29.492, excluded_from_total=True),
        StartupMark("preload_language", 31.592),
    ]

    logger = _CapturingLogger()
    timeline.log(logger=logger)

    assert logger.warnings
    warning_message, warning_args = logger.warnings[0]
    assert (
        warning_message
        == "startup.total exceeded budget: %.3fs > %.3fs; slowest stages: %s"
    )
    assert warning_args[0] == pytest.approx(9.8)
    assert warning_args[1] == pytest.approx(8.0)
    slowest = warning_args[2]
    assert "build_gui=5.200s" in slowest
    assert "process_streams=2.500s" in slowest
    assert "preload_language=2.100s" in slowest
    assert "welcome_interaction" not in slowest


def test_bootstrap_marks_welcome_interaction_as_excluded() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(
        Path("src/app/bootstrap.py").read_text(encoding="utf-8"),
        filename="src/app/bootstrap.py",
    )
    marks: dict[str, bool] = {}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "timeline"
            and node.func.attr == "mark"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            continue
        excluded = next(
            (
                keyword.value.value
                for keyword in node.keywords
                if keyword.arg == "excluded_from_total"
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, bool)
            ),
            False,
        )
        marks[node.args[0].value] = excluded

    assert marks.get("welcome_interaction") is True
    assert "welcome_gate" not in marks


def test_bootstrap_logging_uses_utf8_filehandler_without_duplicate_handlers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    log_path = tmp_path / "tool.log"

    monkeypatch.delenv("MIO_DEBUG_PIL_LOGS", raising=False)
    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = []

        bootstrap._configure_logging()
        bootstrap._configure_logging()

        assert root_logger.level == bootstrap.logging.DEBUG
        assert len(root_logger.handlers) == 1

        handler = root_logger.handlers[0]
        assert isinstance(handler, bootstrap.logging.FileHandler)
        assert getattr(handler, bootstrap._MIO_FILE_HANDLER_ATTR) is True
        assert getattr(handler, bootstrap._MIO_FILE_HANDLER_PATH_ATTR) == str(
            log_path.resolve()
        )
        assert getattr(handler, "baseFilename") == str(log_path.resolve())
        assert handler.level == bootstrap.logging.DEBUG
        assert handler.formatter is not None
        assert handler.formatter._fmt == bootstrap._LOG_FORMAT
        assert (
            getattr(handler.stream, "encoding", "").lower().replace("-", "") == "utf8"
        )
        assert {
            logger_name: bootstrap.logging.getLogger(logger_name).level
            for logger_name in pil_logger_names
        } == {
            "PIL": bootstrap.logging.WARNING,
            "PIL.Image": bootstrap.logging.WARNING,
            "PIL.PngImagePlugin": bootstrap.logging.WARNING,
        }
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_preserves_existing_handlers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import src.app.bootstrap as bootstrap

    class ExistingHandler(bootstrap.logging.Handler):
        def emit(self, record: bootstrap.logging.LogRecord) -> None:
            return None

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    existing_handler = ExistingHandler()
    log_path = tmp_path / "tool.log"

    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = [existing_handler]

        bootstrap._configure_logging()
        bootstrap._configure_logging()

        assert existing_handler in root_logger.handlers
        mio_file_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, bootstrap._MIO_FILE_HANDLER_PATH_ATTR, None)
            == str(log_path.resolve())
        ]
        assert len(mio_file_handlers) == 1
    finally:
        for handler in list(root_logger.handlers):
            if handler is not existing_handler:
                handler.close()
            root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_replaces_mio_file_handler_for_different_log_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    first_log_path = tmp_path / "first.log"
    second_log_path = tmp_path / "second.log"
    current_log_path = {"value": first_log_path}

    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(
        bootstrap, "get_tool_log", lambda: str(current_log_path["value"])
    )

    try:
        root_logger.handlers[:] = []

        bootstrap._configure_logging()
        current_log_path["value"] = second_log_path
        bootstrap._configure_logging()
        bootstrap._configure_logging()

        mio_file_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, bootstrap._MIO_FILE_HANDLER_ATTR, False)
        ]
        assert len(mio_file_handlers) == 1
        assert getattr(
            mio_file_handlers[0], bootstrap._MIO_FILE_HANDLER_PATH_ATTR
        ) == str(second_log_path.resolve())
        assert first_log_path.is_file()
        assert second_log_path.is_file()
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_reads_runtime_state_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    log_path = tmp_path / "tool.log"
    calls = {"require_states": 0}

    def fake_require_states() -> SimpleNamespace:
        calls["require_states"] += 1
        return SimpleNamespace(development=False)

    monkeypatch.setattr(bootstrap, "require_states", fake_require_states)
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = []

        bootstrap._configure_logging()

        assert calls["require_states"] == 1
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_pil_noise_suppression_can_be_disabled_for_image_debugging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.app.bootstrap as bootstrap

    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }

    monkeypatch.setenv("MIO_DEBUG_PIL_LOGS", "1")

    try:
        for logger_name in pil_logger_names:
            bootstrap.logging.getLogger(logger_name).setLevel(bootstrap.logging.DEBUG)

        bootstrap._suppress_pillow_debug_noise()

        assert {
            logger_name: bootstrap.logging.getLogger(logger_name).level
            for logger_name in pil_logger_names
        } == {
            "PIL": bootstrap.logging.DEBUG,
            "PIL.Image": bootstrap.logging.DEBUG,
            "PIL.PngImagePlugin": bootstrap.logging.DEBUG,
        }
    finally:
        for logger_name, level in old_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_preserves_existing_stream_handler_and_adds_file_handler(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import io
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    existing_stream_handler = bootstrap.logging.StreamHandler(io.StringIO())
    log_path = tmp_path / "tool.log"

    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = [existing_stream_handler]

        bootstrap._configure_logging()

        assert existing_stream_handler in root_logger.handlers
        mio_file_handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, bootstrap.logging.FileHandler)
            and getattr(handler, bootstrap._MIO_FILE_HANDLER_PATH_ATTR, None)
            == str(log_path.resolve())
        ]
        assert len(mio_file_handlers) == 1
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_reuses_existing_unmarked_file_handler_for_same_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    log_path = tmp_path / "tool.log"
    existing_file_handler = bootstrap.logging.FileHandler(
        str(log_path.resolve()), mode="a", encoding="utf-8"
    )

    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = [existing_file_handler]

        bootstrap._configure_logging()
        bootstrap._configure_logging()

        file_handlers_for_path = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, bootstrap.logging.FileHandler)
            and getattr(handler, "baseFilename", None) == str(log_path.resolve())
        ]
        assert file_handlers_for_path == [existing_file_handler]
        assert getattr(existing_file_handler, bootstrap._MIO_FILE_HANDLER_ATTR) is True
        assert getattr(
            existing_file_handler, bootstrap._MIO_FILE_HANDLER_PATH_ATTR
        ) == str(log_path.resolve())
        assert existing_file_handler.level == bootstrap.logging.DEBUG
        assert existing_file_handler.formatter is not None
        assert existing_file_handler.formatter._fmt == bootstrap._LOG_FORMAT
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)


def test_bootstrap_logging_replaces_same_path_non_utf8_file_handler(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import io
    import src.app.bootstrap as bootstrap

    root_logger = bootstrap.logging.getLogger()
    old_handlers = list(root_logger.handlers)
    old_root_level = root_logger.level
    pil_logger_names = ("PIL", "PIL.Image", "PIL.PngImagePlugin")
    old_pil_levels = {
        logger_name: bootstrap.logging.getLogger(logger_name).level
        for logger_name in pil_logger_names
    }
    log_path = tmp_path / "tool.log"
    existing_stream_handler = bootstrap.logging.StreamHandler(io.StringIO())
    existing_file_handler = bootstrap.logging.FileHandler(
        str(log_path.resolve()), mode="a", encoding="cp1251"
    )

    monkeypatch.setattr(
        bootstrap, "require_states", lambda: SimpleNamespace(development=False)
    )
    monkeypatch.setattr(bootstrap, "get_tool_log", lambda: str(log_path))

    try:
        root_logger.handlers[:] = [existing_stream_handler, existing_file_handler]

        bootstrap._configure_logging()
        bootstrap._configure_logging()

        assert existing_stream_handler in root_logger.handlers
        assert existing_file_handler not in root_logger.handlers
        file_handlers_for_path = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, bootstrap.logging.FileHandler)
            and getattr(handler, "baseFilename", None) == str(log_path.resolve())
        ]
        assert len(file_handlers_for_path) == 1
        replacement = file_handlers_for_path[0]
        assert replacement is not existing_file_handler
        assert getattr(replacement, bootstrap._MIO_FILE_HANDLER_ATTR) is True
        assert getattr(replacement, bootstrap._MIO_FILE_HANDLER_PATH_ATTR) == str(
            log_path.resolve()
        )
        assert (
            getattr(replacement.stream, "encoding", "")
            .lower()
            .replace("-", "")
            .replace("_", "")
            == "utf8"
        )
    finally:
        for handler in list(root_logger.handlers):
            try:
                handler.close()
            finally:
                root_logger.removeHandler(handler)
        if existing_file_handler not in root_logger.handlers:
            existing_file_handler.close()
        for handler in old_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(old_root_level)
        for logger_name, level in old_pil_levels.items():
            bootstrap.logging.getLogger(logger_name).setLevel(level)

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
