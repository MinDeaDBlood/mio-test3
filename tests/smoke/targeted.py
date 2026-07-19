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


import pytest



_CONTRACT_PATHS = [
    'tests/contract/logic/test_controller_contracts.py',
    'tests/contract/projects/import_flow/test_import_flow_contracts.py',
    'tests/contract/projects/unpack/test_workflow_contracts.py',
    'tests/contract/projects/pack/test_partition_contracts.py',
    'tests/contract/plugins/test_store_service_contracts.py',
    'tests/unit/plugins',
    'tests/integration/plugins',
    'tests/functional/repository',
    'tests/architecture/test_file_dialog_async_boundary.py',
    'tests/contract/update/test_update_contracts.py',
    'tests/contract/localization/test_localization_and_settings_contracts.py',
    'tests/contract/app/test_runtime_boundary_contracts.py',
    'tests/architecture/test_ui_task_runner_adoption.py',
    'tests/architecture/test_lazy_heavy_surface_cleanup.py',
    'tests/regression/test_public_contracts.py',
]


def main() -> None:
    exit_code = pytest.main(['-q', *_CONTRACT_PATHS])
    if exit_code != pytest.ExitCode.OK:
        raise SystemExit(int(exit_code))
    print('TARGETED_CONTROLLER_TESTS_OK')


if __name__ == '__main__':
    main()
