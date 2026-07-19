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



def pytest_collection_modifyitems(config, items):
    """Keep in-process contracts separate from subprocess-heavy checks.

    Unit/architecture contracts run first. Release/dependency subprocess checks
    run near the end so any slow external process cannot influence in-process
    import/runtime contract ordering. GUI smoke wrappers are skipped by default
    and remain explicit.
    """

    def _priority(item):
        path = str(item.path).replace('\\', '/')
        if path.endswith('/tests/architecture/test_startup_entrypoint_lazy_boundary.py'):
            return (0, path, item.name)
        if path.endswith('/tests/architecture/test_removed_legacy_boundaries.py'):
            return (0, path, item.name)
        if path.endswith('/tests/external/test_runtime_dependencies.py') or path.endswith('/tests/release/test_release_reproducibility.py'):
            return (8, path, item.name)
        if path.endswith('/tests/contract/scripts/test_smoke_scripts.py'):
            return (9, path, item.name)
        return (3, path, item.name)

    explicit_smoke_scripts = any(str(arg).replace('\\', '/').endswith('tests/contract/scripts/test_smoke_scripts.py') for arg in config.args)
    run_gui_smoke = explicit_smoke_scripts
    if not run_gui_smoke:
        import os
        run_gui_smoke = os.environ.get('MIO_RUN_GUI_SMOKE_IN_PYTEST') == '1'

    import pytest
    if not explicit_smoke_scripts:
        skip_external_smoke = pytest.mark.skip(reason='External smoke scripts run via scripts/manual/runtime_smoke_suite.py or explicit tests/contract/scripts/test_smoke_scripts.py invocation')
        for item in items:
            path = str(item.path).replace('\\', '/')
            if path.endswith('/tests/contract/scripts/test_smoke_scripts.py'):
                item.add_marker(skip_external_smoke)
    elif not run_gui_smoke:
        skip_gui_smoke = pytest.mark.skip(reason='GUI smoke scripts run via scripts/manual/runtime_smoke_suite.py or MIO_RUN_GUI_SMOKE_IN_PYTEST=1')
        for item in items:
            path = str(item.path).replace('\\', '/')
            if path.endswith('/tests/contract/scripts/test_smoke_scripts.py') and 'gui' in item.keywords:
                item.add_marker(skip_gui_smoke)

    items.sort(key=_priority)

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
