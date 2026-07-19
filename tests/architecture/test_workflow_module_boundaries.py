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
def _source(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding='utf-8')


def _imports(relative: str) -> set[str]:
    tree = ast.parse(_source(relative), filename=relative)
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def test_unpack_service_remains_a_thin_orchestrator() -> None:
    relative = 'src/logic/projects/unpack/workflow/service.py'
    source = _source(relative)
    imports = _imports(relative)

    assert len(source.splitlines()) <= 150
    assert not imports.intersection(
        {
            'src.core.payload_extract',
            'src.core.lpunpack',
            'src.core.splituapp',
            'src.core.imgextractor',
            'zipfile',
            'subprocess',
        }
    )
    assert 'extract_payload_images(source, chose, output=output)' in source
    assert 'extract_super_images(source, chose, parts, json_edit, output=output)' in source
    assert 'extract_update_app_images(source, chose)' in source


def test_mtk_operation_remains_a_stage_orchestrator() -> None:
    relative = 'src/logic/tools/mtk_port_tool/operation.py'
    source = _source(relative)
    imports = _imports(relative)

    assert len(source.splitlines()) <= 80
    assert not imports.intersection(
        {
            'subprocess',
            'zipfile',
            'shutil',
            'src.core.Magisk',
            'src.core.imgextractor',
            'src.core.ota_dat',
        }
    )
    for stage in ('_decompress_portzip()', '_port_boot()', '_port_system()', '_pack_img()', '_pack_rom()', 'clean()'):
        assert stage in source


def test_bootstrap_delegates_logging_setup_to_platform_module() -> None:
    bootstrap = _source('src/app/bootstrap.py')
    logging_module = _source('src/platform/logging_setup.py')
    crash_logging_module = _source('src/platform/crash_logging.py')

    assert len(bootstrap.splitlines()) <= 400
    assert 'logging_setup.configure_logging(' in bootstrap
    assert 'logging.FileHandler(' not in bootstrap
    assert 'initialize_process_logging(' in logging_module
    assert 'RotatingFileHandler(' in crash_logging_module


def test_ui_service_output_only_renders_and_app_owns_composition() -> None:
    ui_source = _source('src/ui/common/service_output.py')
    app_source = _source('src/app/composition/service_output.py')

    assert 'build_service_output' not in ui_source
    assert 'def build_ui_service_output' not in ui_source
    assert 'UiServiceOutputSink' in ui_source
    assert 'build_service_output' in app_source
    assert 'def build_ui_service_output' in app_source

def test_ui_does_not_build_logic_requests() -> None:
    ui_root = PROJECT_ROOT / 'src' / 'ui'
    violations: list[str] = []
    for path in sorted(ui_root.rglob('*.py')):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=relative)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in {'build_request', 'create_request'}:
                violations.append(f'{relative}:{node.lineno}:{node.func.attr}')
    assert violations == []


def test_ui_runtime_does_not_import_logic_request_types() -> None:
    ui_root = PROJECT_ROOT / 'src' / 'ui'
    violations: list[str] = []

    def visit(node: ast.AST, *, type_checking: bool = False) -> None:
        if isinstance(node, ast.If):
            is_type_checking = isinstance(node.test, ast.Name) and node.test.id == 'TYPE_CHECKING'
            for child in node.body:
                visit(child, type_checking=type_checking or is_type_checking)
            for child in node.orelse:
                visit(child, type_checking=type_checking)
            return
        if (
            not type_checking
            and isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith('src.logic')
        ):
            for alias in node.names:
                if alias.name.endswith('Request'):
                    violations.append(f'{node.module}.{alias.name}:{node.lineno}')
        for child in ast.iter_child_nodes(node):
            visit(child, type_checking=type_checking)

    for path in sorted(ui_root.rglob('*.py')):
        visit(ast.parse(path.read_text(encoding='utf-8'), filename=str(path)))
    assert violations == []

def test_owned_ui_app_and_logic_modules_stay_reviewable_in_size() -> None:
    oversized: list[str] = []
    for layer in ('ui', 'app', 'logic'):
        for path in sorted((PROJECT_ROOT / 'src' / layer).rglob('*.py')):
            line_count = len(path.read_text(encoding='utf-8').splitlines())
            if line_count > 400:
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                oversized.append(f'{relative}:{line_count}')
    assert oversized == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
