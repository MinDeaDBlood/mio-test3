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


import io

import pytest

from src.core.PySquashfsImage.util import find_superblocks
from src.logic.plugins.runtime import (
    Entry,
    PluginInvocationError,
    PluginLoader,
    PluginRegistrationError,
)


def test_plugin_loader_does_not_retry_after_internal_type_error() -> None:
    loader = PluginLoader()
    calls = []

    def plugin(value):
        calls.append(value)
        raise TypeError('plugin implementation failed')

    loader.register('broken', Entry.main, plugin)

    with pytest.raises(TypeError, match='plugin implementation failed'):
        loader.run('broken', Entry.main, mapped_args={'value': 'one call'})

    assert calls == ['one call']


def test_plugin_loader_reports_missing_required_mapped_argument() -> None:
    loader = PluginLoader()
    loader.register('strict', Entry.main, lambda required: required)

    with pytest.raises(PluginInvocationError, match="Required argument 'required' is missing"):
        loader.run('strict', Entry.main, mapped_args={})


def test_plugin_loader_rejects_unregistered_entry() -> None:
    loader = PluginLoader()

    with pytest.raises(PluginRegistrationError, match='not registered'):
        loader.run('missing', Entry.main)


def test_squashfs_scanner_accepts_explicit_stream_and_bytes_inputs() -> None:
    assert find_superblocks(io.BytesIO(b'not squashfs')) == []
    assert find_superblocks(b'not squashfs') == []


def test_squashfs_scanner_rejects_ambiguous_input_type() -> None:
    with pytest.raises(TypeError, match='seekable binary stream'):
        find_superblocks(123)

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
