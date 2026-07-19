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

from .layer_rules import (
    _static_src_import_graph,
    _strongly_connected_components,
    check_ci_wrapper_exit_boundary,
)
from .reporting import FAIL, PASS, GuardContext, read_text, record_violation


_REMOVED_SURFACES = (
    "src/core/utils.py",
    "src/core/images.py",
    "src/core/miside_banner.py",
    "src/core/runtime_flags.py",
    "src/core/addon_register.py",
    "src/core/help_suggestions.py",
    "src/core/version_control.py",
    "src/core/module_errors.py",
    "src/core/threading_utils.py",
    "src/core/mkc_filedialog.py",
    "src/core/ui_geometry.py",
    "src/app/runtime_state.py",
    "src/app/runtime_compat.py",
    "src/app/runtime_accessors.py",
    "src/app/runtime/decorators.py",
    "src/app/localization_aliases.py",
    "src/app/tk_runtime.py",
    "src/ui/tabs/project/common.py",
    "src/ui/tabs/project/pack/hybrid/window.py",
    "src/ui/plugins/runtime_context.py",
    "src/ui/common/file_dialog_backend.py",
    "src/ui/tabs/plugins/module_dialogs.py",
    "src/ui/tabs/tools/download_firmware/window.py",
    "src/app/dialogs.py",
    "src/app/errors.py",
    "src/app/runtime/contexts/dialogs.py",
    "src/app/runtime/contexts/common.py",
    "src/app/welcome/composition.py",
    "src/logic/log_interface/runtime_context.py",
    "src/app/plugins/store/controller.py",
    "src/app/plugins/store/catalog_refresh.py",
    "src/porttool",
    "src/ui/home/file_picker/button.py",
    "src/ui/plugins/editor_launcher.py",
    "src/ui/window_sections/input_actions.py",
    "src/core/formatting.py",
    "src/ui/bug_report/submit",
    "src/ui/tool.py",
    "src/app/core_diagnostics.py",
    "src/app/settings/cache_service.py",
    "src/app/settings/language_repository.py",
    "src/app/welcome/content_repository.py",
    "src/logic/bug_report/controller.py",
    "src/logic/bug_report/runtime_context.py",
    "src/logic/bug_report/report.py",
    "src/logic/bug_report/submitter",
    "src/logic/projects/actions.py",
    "bin/setting.ini",
    "bin/configs.json",
    "bin/context_rules.json",
    "bin/plugin_db.json",
    "bin/languages",
    "bin/config",
    "src/config",
    "src/infrastructure",
)

_UI_OPERATIONAL_IMPORTS = {
    "subprocess",
    "shutil",
    "zipfile",
    "tarfile",
    "threading",
    "multiprocessing",
    "webbrowser",
}

_UI_FORBIDDEN_CALLS = {
    "print",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "shutil.copy",
    "shutil.copy2",
    "shutil.copyfile",
    "shutil.copytree",
    "shutil.move",
    "shutil.rmtree",
    "zipfile.ZipFile",
    "tarfile.open",
    "threading.Thread",
    "multiprocessing.Process",
}

_LOGIC_PRESENTATION_TOKENS = (
    "message_pop(",
    "UiNotifier",
    "UiDispatcher",
    "UiTaskRunner",
    "color='red'",
    'color="red"',
    "color='green'",
    'color="green"',
    ".configure(text=",
    ".config(text=",
)

_APP_UI_ALLOWED_PREFIXES = (
    "src/app/composition/",
    "src/app/bootstrap.py",
    "src/app/window_launchers.py",
)


def _module_name(path: Path, src_dir: Path) -> str:
    rel = path.relative_to(src_dir).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return "src" + ("." + ".".join(parts) if parts else "")


def _imports(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(read_text(path), filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
    return found


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.AST = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


_UI_FORBIDDEN_LOGIC_RUNTIME_SUFFIXES = (
    "Controller",
    "Factory",
    "Repository",
    "Request",
    "Service",
    "UseCase",
)


def _is_type_checking_test(node: ast.AST) -> bool:
    return (isinstance(node, ast.Name) and node.id == "TYPE_CHECKING") or (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "typing"
        and node.attr == "TYPE_CHECKING"
    )


def _runtime_logic_service_imports(tree: ast.AST) -> list[tuple[int, str, str]]:
    found: list[tuple[int, str, str]] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.If) and _is_type_checking_test(node.test):
            for child in node.orelse:
                visit(child)
            return
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("src.logic")
        ):
            for alias in node.names:
                if alias.name.endswith(_UI_FORBIDDEN_LOGIC_RUNTIME_SUFFIXES):
                    found.append((node.lineno, node.module, alias.name))
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return found


def check_current_layer_dependencies(ctx: GuardContext) -> None:
    print("\n-- Current layer dependency audit --")
    violations = 0
    for path in sorted(ctx.src_dir.rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        module = _module_name(path, ctx.src_dir)
        for lineno, imported in _imports(path):
            reason = None
            if module == "src.core" or module.startswith("src.core."):
                if imported == "tkinter" or imported.startswith("tkinter."):
                    reason = "core must not depend on Tkinter"
                elif imported == "src.app" or imported.startswith("src.app."):
                    reason = "core must not depend on app"
                elif imported == "src.platform" or imported.startswith("src.platform."):
                    reason = "core must not depend on platform adapters"
                elif imported == "src.logic" or imported.startswith("src.logic."):
                    reason = "core must not depend on logic"
                elif imported == "src.ui" or imported.startswith("src.ui."):
                    reason = "core must not depend on ui"
            elif module == "src.logic" or module.startswith("src.logic."):
                if imported == "tkinter" or imported.startswith("tkinter."):
                    reason = "logic must not depend on Tkinter"
                elif imported == "src.app" or imported.startswith("src.app."):
                    reason = "logic must not depend on app"
                elif imported == "src.ui" or imported.startswith("src.ui."):
                    reason = "logic must not depend on ui"
                elif imported == "src.platform" or imported.startswith("src.platform."):
                    reason = "logic must receive platform resources through explicit inputs"
            elif module == "src.platform" or module.startswith("src.platform."):
                if imported == "src.app" or imported.startswith("src.app."):
                    reason = "platform must not depend on app"
                elif imported == "src.logic" or imported.startswith("src.logic."):
                    reason = "platform adapters must not contain domain decisions"
                elif imported == "src.ui" or imported.startswith("src.ui."):
                    reason = "platform must not depend on ui"
            elif module == "src.ui" or module.startswith("src.ui."):
                if imported == "src.app" or imported.startswith("src.app."):
                    reason = "ui must receive application services through injected presentation ports"
                elif imported == "src.logic" or imported.startswith("src.logic."):
                    reason = "ui must use structural presentation ports instead of logic models"
                elif imported == "src.core" or imported.startswith("src.core."):
                    reason = "ui must not depend on core implementation details"
                elif imported == "src.platform" or imported.startswith("src.platform."):
                    reason = (
                        "ui must receive platform actions from application composition"
                    )
            if reason:
                violations += 1
                record_violation(ctx, f"  {FAIL} {rel}:{lineno} — {reason}: {imported}")
    if violations == 0:
        print(
            f"  {PASS} core, logic, platform, app, and UI dependencies respect strict layer direction"
        )


def check_current_static_import_cycles(ctx: GuardContext) -> None:
    print("\n-- Static src import-cycle audit --")
    graph = _static_src_import_graph(ctx.project_root)
    cycles = [
        component
        for component in _strongly_connected_components(graph)
        if len(component) > 1
    ]
    if cycles:
        for component in cycles:
            record_violation(
                ctx, f"  {FAIL} static import cycle: {' -> '.join(sorted(component))}"
            )
        return
    print(f"  {PASS} No static import cycles detected across src/")


def check_removed_surfaces_stay_removed(ctx: GuardContext) -> None:
    print("\n-- Removed compatibility surface audit --")
    found = [rel for rel in _REMOVED_SURFACES if (ctx.project_root / rel).exists()]
    if found:
        for rel in found:
            record_violation(
                ctx,
                f"  {FAIL} {rel} — removed mixed or compatibility surface must not return",
            )
        return
    print(f"  {PASS} Removed mixed and compatibility surfaces stay deleted")


def check_core_ownership(ctx: GuardContext) -> None:
    print("\n-- Core ownership audit --")
    violations = 0
    forbidden_names = {
        "lang",
        "message_pop",
        "UiNotifier",
        "UiDispatcher",
        "UiTaskRunner",
    }
    for path in sorted((ctx.src_dir / "core").rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        source = read_text(path)
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — presentation/application name leaked into core: {node.id}",
                )
        if "runtime_state" in source or "message_pop(" in source:
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} {rel} — application runtime or UI feedback leaked into core",
            )
    if violations == 0:
        print(f"  {PASS} core contains low-level operations and data formats only")


def check_core_library_io_boundary(ctx: GuardContext) -> None:
    print("\n-- Core library I/O boundary audit --")
    violations = 0
    for path in sorted((ctx.src_dir / "core").rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        tree = ast.parse(read_text(path), filename=str(path))
        sys_aliases: set[str] = set()
        imported_exit_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sys":
                        sys_aliases.add(alias.asname or "sys")
            elif isinstance(node, ast.ImportFrom) and node.module == "sys":
                for alias in node.names:
                    if alias.name == "exit":
                        imported_exit_names.add(alias.asname or alias.name)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call = _call_name(node)
            if isinstance(node.func, ast.Name) and node.func.id in {"print", "input"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — core library must use diagnostics or injected I/O instead of {node.func.id}()",
                )
            elif isinstance(node.func, ast.Name) and node.func.id in {"exit", "quit"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — core library must raise a typed exception instead of {node.func.id}()",
                )
            elif (
                isinstance(node.func, ast.Name) and node.func.id in imported_exit_names
            ):
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — core library must raise a typed exception instead of sys.exit()",
                )
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "exit"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in sys_aliases
            ):
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — core library must raise a typed exception instead of sys.exit()",
                )
            elif call in {"builtins.input", "builtins.print"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — core library must use diagnostics instead of {call}()",
                )
    if violations == 0:
        print(
            f"  {PASS} core uses diagnostics and typed errors instead of console control flow"
        )


def check_logic_ownership(ctx: GuardContext) -> None:
    print("\n-- Logic ownership audit --")
    violations = 0
    for path in sorted((ctx.src_dir / "logic").rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        source = read_text(path)
        tree = ast.parse(source, filename=str(path))
        leaked = [token for token in _LOGIC_PRESENTATION_TOKENS if token in source]
        if leaked:
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} {rel} — presentation behavior leaked into logic: {', '.join(leaked)}",
            )
        for token in (
            "resolve_ui_host_window",
            "resolve_root",
            "resolve_main_window",
            "build_ui_task_runner",
            "build_ui_dispatcher",
        ):
            if token in source:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel} — application/UI runtime resolver leaked into logic: {token}",
                )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call = _call_name(node)
            if isinstance(node.func, ast.Name) and node.func.id in {"print", "input"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — logic must publish output through ServiceOutput instead of {node.func.id}()",
                )
            elif isinstance(node.func, ast.Name) and node.func.id in {"exit", "quit"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — logic must return a result or raise a typed exception instead of {node.func.id}()",
                )
            elif call in {"sys.exit", "builtins.input"}:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — logic must return a result or raise a typed exception instead of {call}()",
                )
    if violations == 0:
        print(
            f"  {PASS} logic stays independent from presentation, application runtime, and console control flow"
        )


def _is_legacy_localization_key(value: str) -> bool:
    return (value.startswith("text") and value[4:].isdigit()) or (
        value.startswith("t") and value[1:].isdigit()
    )


def check_ui_localization_boundary(ctx: GuardContext) -> None:
    print("\n-- UI localization boundary audit --")
    violations = 0
    localization_path = ctx.src_dir / "ui" / "localization.py"
    if not localization_path.exists():
        record_violation(
            ctx,
            f"  {FAIL} src/ui/localization.py — LocalizationCatalog protocol is missing",
        )
        return

    localization_source = read_text(localization_path)
    localization_tree = ast.parse(localization_source, filename=str(localization_path))
    for node in localization_tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(
            isinstance(target, ast.Name) and target.id == "lang" for target in targets
        ):
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} src/ui/localization.py:{node.lineno} — UI localization must not expose a process-wide lang object",
            )
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ) and node.name in {"bind_localization", "UiLocalizationContext"}:
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} src/ui/localization.py:{node.lineno} — hidden localization binding must not return: {node.name}",
            )

    for layer in ("ui", "app"):
        for path in sorted((ctx.src_dir / layer).rglob("*.py")):
            rel = path.relative_to(ctx.project_root).as_posix()
            source = read_text(path)
            if layer == "ui" and (
                "from src.ui.localization import lang" in source
                or "src.ui.localization.lang" in source
            ):
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel} — UI must receive LocalizationCatalog explicitly instead of importing lang",
                )
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                key = None
                if isinstance(node, ast.Attribute):
                    key = node.attr
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    key = node.value
                if key is not None and _is_legacy_localization_key(key):
                    violations += 1
                    record_violation(
                        ctx,
                        f"  {FAIL} {rel}:{node.lineno} — semantic localization key required instead of {key}",
                    )
    if violations == 0:
        print(
            f"  {PASS} UI localization is explicit and UI/application code uses semantic keys"
        )


def check_ui_ownership(ctx: GuardContext) -> None:
    print("\n-- UI ownership audit --")
    violations = 0
    for path in sorted((ctx.src_dir / "ui").rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        source = read_text(path)
        tree = ast.parse(source, filename=str(path))
        for lineno, imported in _imports(path):
            root = imported.split(".", 1)[0]
            if root in _UI_OPERATIONAL_IMPORTS:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{lineno} — operational module must not be imported by UI: {imported}",
                )
        for lineno, module, imported_name in _runtime_logic_service_imports(tree):
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} {rel}:{lineno} — UI must not runtime-import logic service types: {module}.{imported_name}",
            )
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call = _call_name(node)
                if call in _UI_FORBIDDEN_CALLS:
                    violations += 1
                    record_violation(
                        ctx,
                        f"  {FAIL} {rel}:{node.lineno} — operational call must stay outside UI: {call}",
                    )
                if call.endswith((".build_request", ".create_request")):
                    violations += 1
                    record_violation(
                        ctx,
                        f"  {FAIL} {rel}:{node.lineno} — application controller must build domain requests outside UI: {call}",
                    )
        for token in (
            "build_ui_task_runner(",
            "build_ui_dispatcher(",
            "resolve_settings(",
            "resolve_project_manager(",
            "resolve_ui_host_window(",
        ):
            if token in source:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel} — UI must receive dependencies explicitly instead of resolving or building them: {token}",
                )
    if violations == 0:
        print(
            f"  {PASS} UI contains presentation behavior and receives operational dependencies explicitly"
        )


def check_app_ui_composition_boundary(ctx: GuardContext) -> None:
    print("\n-- App to UI composition boundary audit --")
    violations = 0
    for path in sorted((ctx.src_dir / "app").rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        ui_imports = [
            (lineno, imported)
            for lineno, imported in _imports(path)
            if imported == "src.ui" or imported.startswith("src.ui.")
        ]
        if not ui_imports:
            continue
        if any(
            rel == prefix or rel.startswith(prefix)
            for prefix in _APP_UI_ALLOWED_PREFIXES
        ):
            continue
        for lineno, imported in ui_imports:
            violations += 1
            record_violation(
                ctx,
                f"  {FAIL} {rel}:{lineno} — app may import concrete UI only from composition/startup boundaries: {imported}",
            )
    if violations == 0:
        print(
            f"  {PASS} Concrete UI imports stay inside app composition and startup boundaries"
        )


def check_runtime_ownership(ctx: GuardContext) -> None:
    print("\n-- Runtime ownership audit --")
    violations = 0
    forbidden_legacy_tokens = (
        "src.app.runtime_state",
        "src.app.runtime_compat",
        "src.app.runtime_accessors",
        "src.app.tk_runtime",
    )
    for path in sorted(ctx.src_dir.rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        source = read_text(path)
        for token in forbidden_legacy_tokens:
            if token in source:
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel} — legacy runtime facade reference remains: {token}",
                )
        if rel.startswith(("src/ui/", "src/logic/", "src/core/")):
            for lineno, imported in _imports(path):
                if imported == "src.app.runtime" or imported.startswith(
                    "src.app.runtime."
                ):
                    violations += 1
                    record_violation(
                        ctx,
                        f"  {FAIL} {rel}:{lineno} — runtime access must stay in app: {imported}",
                    )
    if not (ctx.project_root / "src/app/runtime").is_dir():
        violations += 1
        record_violation(
            ctx, f"  {FAIL} src/app/runtime — typed runtime package is missing"
        )
    if violations == 0:
        print(f"  {PASS} Runtime access is centralized under src/app/runtime")


def check_no_base_exception_catches(ctx: GuardContext) -> None:
    print("\n-- Exception boundary audit --")
    violations = 0
    for path in sorted(ctx.src_dir.rglob("*.py")):
        rel = path.relative_to(ctx.project_root).as_posix()
        tree = ast.parse(read_text(path), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or node.type is None:
                continue
            caught: list[ast.AST]
            if isinstance(node.type, ast.Tuple):
                caught = list(node.type.elts)
            else:
                caught = [node.type]
            if any(
                isinstance(item, ast.Name) and item.id == "BaseException"
                for item in caught
            ):
                violations += 1
                record_violation(
                    ctx,
                    f"  {FAIL} {rel}:{node.lineno} — BaseException must not be handled as an operational failure",
                )
    if violations == 0:
        print(f"  {PASS} Operational code does not swallow BaseException")


def check_feature_separation(ctx: GuardContext) -> None:
    print("\n-- Feature separation audit --")
    required = (
        "src/logic/projects/pack/hybrid/service.py",
        "src/app/projects/pack/hybrid_action.py",
        "src/ui/tabs/project/pack/hybrid/device_prompt.py",
        "src/logic/projects/pack/postinstall/repository.py",
        "src/app/projects/pack/postinstall_controller.py",
        "src/ui/tabs/project/pack/postinstall/editor_window.py",
        "src/app/update_controller.py",
        "src/ui/update/window.py",
        "src/app/plugins/store/fetch_flow.py",
        "src/ui/tabs/plugins/store/window.py",
    )
    missing = [rel for rel in required if not (ctx.project_root / rel).exists()]
    if missing:
        for rel in missing:
            record_violation(
                ctx, f"  {FAIL} {rel} — required separated feature boundary is missing"
            )
        return
    print(
        f"  {PASS} Hybrid, postinstall, updater, and Plugin Store have separate UI, app, and logic boundaries"
    )


__all__ = [
    "check_app_ui_composition_boundary",
    "check_ci_wrapper_exit_boundary",
    "check_core_library_io_boundary",
    "check_core_ownership",
    "check_current_layer_dependencies",
    "check_current_static_import_cycles",
    "check_feature_separation",
    "check_logic_ownership",
    "check_no_base_exception_catches",
    "check_removed_surfaces_stay_removed",
    "check_runtime_ownership",
    "check_ui_localization_boundary",
    "check_ui_ownership",
]

if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
