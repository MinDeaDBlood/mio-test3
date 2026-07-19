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
from pathlib import Path

from .reporting import FAIL, PASS, GuardContext, read_text, record_violation


def _module_name_for_path(project_root: Path, path: Path) -> str:
    parts = path.relative_to(project_root).with_suffix('').parts
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def _nearest_known_module(imported: str, known_modules: set[str]) -> str | None:
    module = imported
    while module:
        if module in known_modules:
            return module
        if '.' not in module:
            return None
        module = module.rsplit('.', 1)[0]
    return None


def _static_src_import_graph(project_root: Path) -> dict[str, set[str]]:
    py_files = [path for path in (project_root / 'src').rglob('*.py') if path.is_file()]
    module_by_path = {path: _module_name_for_path(project_root, path) for path in py_files}
    known_modules = set(module_by_path.values())
    graph: dict[str, set[str]] = {module: set() for module in known_modules}

    for path, module_name in module_by_path.items():
        try:
            tree = ast.parse(read_text(path), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not alias.name.startswith('src.'):
                        continue
                    imported = _nearest_known_module(alias.name, known_modules)
                    if imported and imported != module_name:
                        graph[module_name].add(imported)
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('src.'):
                imported = _nearest_known_module(node.module, known_modules)
                if imported and imported != module_name:
                    graph[module_name].add(imported)
    return graph


def _strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def strongconnect(module: str) -> None:
        index[module] = len(index)
        lowlink[module] = index[module]
        stack.append(module)
        on_stack.add(module)
        for dependency in sorted(graph.get(module, ())):
            if dependency not in index:
                strongconnect(dependency)
                lowlink[module] = min(lowlink[module], lowlink[dependency])
            elif dependency in on_stack:
                lowlink[module] = min(lowlink[module], index[dependency])
        if lowlink[module] != index[module]:
            return
        component: list[str] = []
        while True:
            dependency = stack.pop()
            on_stack.remove(dependency)
            component.append(dependency)
            if dependency == module:
                break
        if len(component) > 1:
            components.append(sorted(component))

    for module in sorted(graph):
        if module not in index:
            strongconnect(module)
    return sorted(components, key=lambda component: (len(component), component))


def _is_string_constant(node: ast.AST, value: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _is_importlib_os_exit_call(
    node: ast.Call,
    *,
    importlib_aliases: set[str],
    import_module_names: set[str],
) -> bool:
    if not (isinstance(node.func, ast.Attribute) and node.func.attr == '_exit'):
        return False
    import_module_call = node.func.value
    if not isinstance(import_module_call, ast.Call) or not import_module_call.args:
        return False
    if not _is_string_constant(import_module_call.args[0], 'os'):
        return False
    callee = import_module_call.func
    if (
        isinstance(callee, ast.Attribute)
        and callee.attr == 'import_module'
        and isinstance(callee.value, ast.Name)
        and callee.value.id in importlib_aliases
    ):
        return True
    return isinstance(callee, ast.Name) and callee.id in import_module_names


def check_ci_wrapper_exit_boundary(ctx: GuardContext) -> None:
    print('\n-- Process exit boundary audit --')
    violations = 0
    for root_name in ('scripts', 'src', 'tests'):
        root = ctx.project_root / root_name
        if not root.exists():
            continue
        for path in root.rglob('*.py'):
            rel = path.relative_to(ctx.project_root).as_posix()
            try:
                tree = ast.parse(read_text(path), filename=str(path))
            except SyntaxError:
                continue
            os_aliases: set[str] = set()
            importlib_aliases: set[str] = set()
            import_module_names: set[str] = set()
            imported_exit_names: set[str] = set()
            simple_exit_aliases: set[str] = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        local_name = alias.asname or alias.name.split('.', 1)[0]
                        if alias.name == 'os':
                            os_aliases.add(local_name)
                        elif alias.name == 'importlib':
                            importlib_aliases.add(local_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module == 'os':
                        for alias in node.names:
                            if alias.name == '_exit':
                                imported_exit_names.add(alias.asname or alias.name)
                                violations += 1
                                record_violation(ctx, f'  {FAIL} {rel} — from os import _exit is forbidden')
                    elif node.module == 'importlib':
                        for alias in node.names:
                            if alias.name == 'import_module':
                                import_module_names.add(alias.asname or alias.name)
                    elif node.module == 'scripts.support.command_runner' and any(alias.name == 'terminate_process' for alias in node.names):
                        violations += 1
                        record_violation(ctx, f'  {FAIL} {rel} — terminate_process compatibility helper is forbidden')
                elif isinstance(node, ast.Assign):
                    value = node.value
                    is_exit_alias = (
                        isinstance(value, ast.Attribute)
                        and value.attr == '_exit'
                        and isinstance(value.value, ast.Name)
                        and value.value.id in os_aliases
                    ) or (isinstance(value, ast.Name) and value.id in imported_exit_names)
                    if is_exit_alias:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                simple_exit_aliases.add(target.id)
                                violations += 1
                                record_violation(ctx, f'  {FAIL} {rel} — aliasing os._exit is forbidden')

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in os_aliases
                    and node.func.attr == '_exit'
                ):
                    violations += 1
                    record_violation(ctx, f'  {FAIL} {rel} — os._exit is forbidden')
                elif isinstance(node.func, ast.Name) and node.func.id in (imported_exit_names | simple_exit_aliases):
                    violations += 1
                    record_violation(ctx, f'  {FAIL} {rel} — calling an os._exit alias is forbidden')
                elif _is_importlib_os_exit_call(
                    node,
                    importlib_aliases=importlib_aliases,
                    import_module_names=import_module_names,
                ):
                    violations += 1
                    record_violation(ctx, f'  {FAIL} {rel} — importlib.import_module("os")._exit is forbidden')

    if violations == 0:
        print(f'  {PASS} scripts and application code use normal SystemExit semantics without hard process termination')


__all__ = [
    '_static_src_import_graph',
    '_strongly_connected_components',
    'check_ci_wrapper_exit_boundary',
]

if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
