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
import re

from .reporting import FAIL, PASS, WARN, GuardContext, record_violation, run_snippet


def check_compileall(ctx: GuardContext) -> None:
    print('\n-- Compile check --')
    py_files = sorted(ctx.src_dir.rglob('*.py'))
    failures: list[str] = []
    for path in py_files:
        try:
            source = path.read_bytes()
            compile(source, str(path), 'exec', dont_inherit=True)
        except (OSError, SyntaxError, UnicodeError) as exc:
            relative_path = path.relative_to(ctx.project_root)
            failures.append(f'{relative_path}: {exc}')

    if failures:
        for detail in failures:
            record_violation(ctx, f'  {FAIL} compile failed: {detail}')
        return

    print(f'  {PASS} All {len(py_files)} files compile in memory without creating bytecode')



def check_bootstrap_import_surface(ctx: GuardContext) -> None:
    print('\n-- Bootstrap import surface audit --')
    bootstrap_path = ctx.project_root / 'src/app/bootstrap.py'
    source = bootstrap_path.read_text(encoding='utf-8', errors='replace')
    tree = ast.parse(source, filename=str(bootstrap_path))
    forbidden = {
        'PIL.Image': 'PIL image decoding should stay lazy inside bootstrap helpers',
        'src.app.update': 'updater should stay lazily imported inside startup helpers',
        'src.core.images': 'image payloads should stay lazy inside bootstrap helpers',
        'src.ui.common.themes.sv_ttk_fixes': 'theme font overrides should stay lazy inside startup helpers',
        'src.ui.common.titlebar': 'titlebar platform helper should stay lazy inside startup helpers',
        'src.ui.main_window': 'main window should stay lazily imported inside bootstrap helpers',
        'src.ui.tabs.project.common': 'project UI helpers should stay lazily imported inside bootstrap helpers',
        'src.ui.tabs.project.unpack.view': 'unpack UI should stay lazily imported inside bootstrap helpers',
        'src.ui.welcome.wizard': 'welcome wizard should stay lazily imported inside startup helpers',
    }
    count = 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in forbidden:
            count += 1
            record_violation(ctx, f'  {FAIL} src/app/bootstrap.py:{node.lineno} — {forbidden[node.module]}')
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden:
                    count += 1
                    record_violation(ctx, f'  {FAIL} src/app/bootstrap.py:{node.lineno} — {forbidden[alias.name]}')
    if count == 0:
        print(f'  {PASS} bootstrap top-level imports stay boundary-light')



def check_entrypoint_lazy_import_boundary(ctx: GuardContext) -> None:
    print('\n-- Entrypoint lazy import boundary audit --')
    violations = 0

    entrypoint_path = ctx.project_root / 'src/app/entrypoint.py'
    bootstrap_path = ctx.project_root / 'src/app/bootstrap.py'
    process_lifecycle_path = ctx.project_root / 'src/app/process_lifecycle.py'

    entrypoint_source = entrypoint_path.read_text(encoding='utf-8', errors='replace')
    entrypoint_tree = ast.parse(entrypoint_source, filename=str(entrypoint_path))
    for node in entrypoint_tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'src.app.bootstrap':
            violations += 1
            record_violation(ctx, f'  {FAIL} src/app/entrypoint.py:{node.lineno} — entrypoint must import bootstrap lazily inside init/restart')
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'src.app.bootstrap':
                    violations += 1
                    record_violation(ctx, f'  {FAIL} src/app/entrypoint.py:{node.lineno} — entrypoint must import bootstrap lazily inside init/restart')
    for required in ('from src.app.bootstrap import init as _bootstrap_init', 'from src.app.bootstrap import restart as _bootstrap_restart'):
        if required not in entrypoint_source:
            violations += 1
            record_violation(ctx, f'  {FAIL} src/app/entrypoint.py — lazy bootstrap compatibility is incomplete: missing {required}')

    for rel_path, path in (
        ('src/app/bootstrap.py', bootstrap_path),
        ('src/app/process_lifecycle.py', process_lifecycle_path),
    ):
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'), filename=str(path))
        for node in tree.body:
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'tkinter' or alias.name.startswith('tkinter.'):
                        module = alias.name
                        break
            if module == 'tkinter' or (module and module.startswith('tkinter.')):
                violations += 1
                record_violation(ctx, f'  {FAIL} {rel_path}:{node.lineno} — tkinter must stay lazily imported inside startup/runtime functions')

    code = (
        'import importlib, sys\n'
        'importlib.import_module("src.app.entrypoint")\n'
        'loaded = sorted(name for name in sys.modules if name == "tkinter" or name.startswith("tkinter."))\n'
        'print("LOADED=" + ",".join(loaded))\n'
        'raise SystemExit(1 if loaded else 0)\n'
    )
    proc = run_snippet(ctx, code)
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr or '').strip()
        violations += 1
        record_violation(ctx, f'  {FAIL} importing src.app.entrypoint must not load tkinter before startup: {detail}')

    if violations == 0:
        print(f'  {PASS} entrypoint stays lazy and avoids tkinter/bootstrap startup imports')


def check_startup_smoke_imports(ctx: GuardContext) -> None:
    print('\n-- Startup smoke imports --')
    modules = ('src.app.bootstrap', 'src.app.entrypoint')
    for module_name in modules:
        code = 'import importlib\n' f'importlib.import_module({module_name!r})\n' 'print("OK")\n'
        proc = run_snippet(ctx, code)
        if proc.returncode == 0:
            print(f'  {PASS} {module_name} imports without startup crash')
            continue
        stderr = (proc.stderr or '').strip()
        missing_match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", stderr)
        if missing_match and not missing_match.group(1).startswith('src'):
            print(f'  {WARN} {module_name} import skipped by missing external dependency: {missing_match.group(1)}')
            continue
        record_violation(ctx, f'  {FAIL} {module_name} import failed: {stderr.splitlines()[-1] if stderr else proc.stdout.strip()}')

if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
