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


import ast

from tests.support.paths import PROJECT_ROOT

TARGETED_PATH = PROJECT_ROOT / 'tests/smoke/targeted.py'


def _targeted_functions() -> set[str]:
    tree = ast.parse(TARGETED_PATH.read_text(encoding='utf-8'))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _targeted_source() -> str:
    return TARGETED_PATH.read_text(encoding='utf-8')


def test_targeted_runner_is_thin_suite_orchestrator() -> None:
    functions = _targeted_functions()
    assert functions == {'main'}
    source = _targeted_source()
    assert '_CONTRACT_PATHS' in source
    assert "pytest.main(['-q', *_CONTRACT_PATHS])" in source
    assert 'TARGETED_CONTROLLER_TESTS_OK' in source


def test_plugin_store_targeted_contracts_are_split_out_of_god_file() -> None:
    source = _targeted_source()
    assert "'tests/contract/plugins/test_store_service_contracts.py'" in source
    assert "'tests/unit/plugins'" in source
    assert "'tests/integration/plugins'" in source
    assert "'tests/functional/repository'" in source
    assert not (PROJECT_ROOT / 'tests/contract/plugins/test_store_contract_suite.py').exists()
    for moved in {
        '_exercise_plugin_store_catalog_refresh_boundary',
        '_exercise_plugin_store_state_lifecycle_helpers',
        '_exercise_plugin_store_button_state_boundary',
        '_exercise_plugin_store_catalog_filter_boundary',
        '_exercise_plugin_store_catalog_view_model_boundary',
        '_exercise_plugin_store_card_widget_builder_boundary',
    }:
        assert moved not in source


def test_file_dialog_targeted_contract_is_delegated_to_architecture_test() -> None:
    source = _targeted_source()
    assert "'tests/architecture/test_file_dialog_async_boundary.py'" in source
    view_source = (PROJECT_ROOT / 'src/ui/common/mkc_filedialog.py').read_text(encoding='utf-8')
    composition_source = (PROJECT_ROOT / 'src/app/composition/file_dialog.py').read_text(encoding='utf-8')
    assert 'src.app.ui_feedback' not in view_source
    assert 'src.app.ui_tasks' not in view_source
    assert 'src.app.ui_feedback' in composition_source
    assert 'src.app.ui_tasks' in composition_source


def test_pack_partition_contracts_are_delegated_to_domain_tests() -> None:
    source = _targeted_source()
    assert "'tests/contract/projects/pack/test_partition_contracts.py'" in source
    assert 'PackFilesystemHandlerRegistry' not in source
    assert 'scan_packable_super_images' not in source


def test_large_regression_contracts_are_delegated_to_domain_tests() -> None:
    source = _targeted_source()
    assert "'tests/architecture/test_lazy_heavy_surface_cleanup.py'" in source
    assert "'tests/architecture/test_ui_task_runner_adoption.py'" in source
    assert "'tests/regression/test_public_contracts.py'" in source
    assert 'settings_tab_imports = top_level_import_modules' not in source
    assert 'class _FakeListBox' not in source
    assert 'class _WelcomeSettings' not in source


def test_targeted_file_is_final_thin_runner_size() -> None:
    # Final target: the compatibility runner should only orchestrate domain suites.
    assert TARGETED_PATH.stat().st_size < 20_000
    assert len(TARGETED_PATH.read_text(encoding='utf-8').splitlines()) <= 700


def run_all() -> None:
    test_targeted_runner_is_thin_suite_orchestrator()
    test_plugin_store_targeted_contracts_are_split_out_of_god_file()
    test_file_dialog_targeted_contract_is_delegated_to_architecture_test()
    test_pack_partition_contracts_are_delegated_to_domain_tests()
    test_large_regression_contracts_are_delegated_to_domain_tests()
    test_targeted_file_is_final_thin_runner_size()


if __name__ == '__main__':
    run_all()
    print('TARGETED_SPLIT_CONTRACT_TESTS_OK')
