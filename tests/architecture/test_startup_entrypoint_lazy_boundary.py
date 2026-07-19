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
import subprocess
import sys

from tests.support.paths import PROJECT_ROOT
def _top_level_import_modules(path_str: str) -> set[str]:
    tree = ast.parse((PROJECT_ROOT / path_str).read_text(encoding='utf-8'))
    modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_entrypoint_does_not_eagerly_import_bootstrap() -> None:
    imports = _top_level_import_modules('src/app/entrypoint.py')
    assert 'src.app.bootstrap' not in imports
    source = (PROJECT_ROOT / 'src/app/entrypoint.py').read_text(encoding='utf-8')
    assert 'from src.app.bootstrap import init as _bootstrap_init' in source
    assert 'from src.app.bootstrap import restart as _bootstrap_restart' in source


def test_startup_helpers_do_not_import_tkinter_at_module_import_time() -> None:
    for path in ('src/app/bootstrap.py', 'src/app/process_lifecycle.py', 'src/app/window_launchers.py'):
        imports = _top_level_import_modules(path)
        assert 'tkinter' not in imports, path
        assert not any(module.startswith('tkinter.') for module in imports), path


def test_public_entrypoint_import_does_not_load_tkinter_or_bootstrap() -> None:
    code = (
        'import importlib, sys\n'
        'importlib.import_module("src.app.entrypoint")\n'
        'loaded = sorted(name for name in sys.modules if name == "tkinter" or name.startswith("tkinter.") or name == "src.app.bootstrap")\n'
        'print("LOADED=" + ",".join(loaded))\n'
        'raise SystemExit(1 if loaded else 0)\n'
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
