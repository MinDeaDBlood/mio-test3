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


import logging

from src.core.diagnostics import emit, reset_diagnostic_sink, set_diagnostic_sink


def test_default_diagnostic_sink_uses_standard_logging(caplog) -> None:
    with caplog.at_level(logging.INFO, logger='mio.core'):
        emit('operation', 7)

    assert 'operation 7' in caplog.messages


def test_context_diagnostic_sink_is_explicit_and_reversible() -> None:
    messages: list[tuple[object, ...]] = []
    token = set_diagnostic_sink(lambda *parts, **_kwargs: messages.append(parts))
    try:
        emit('step', 1)
    finally:
        reset_diagnostic_sink(token)

    assert messages == [('step', 1)]

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
