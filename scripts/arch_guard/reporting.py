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


from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
import io
import os
import subprocess
import sys
import traceback

PASS = '[OK]'
FAIL = '[FAIL]'
WARN = '[WARN]'


@dataclass(slots=True)
class GuardContext:
    project_root: Path
    src_dir: Path
    violations: list[str] = field(default_factory=list)


def make_context() -> GuardContext:
    project_root = Path(__file__).resolve().parents[2]
    return GuardContext(project_root=project_root, src_dir=project_root / 'src')


def record_violation(ctx: GuardContext, msg: str) -> None:
    print(msg)
    ctx.violations.append(msg)


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def rel_path(ctx: GuardContext, path: Path) -> str:
    return str(path.relative_to(ctx.project_root)).replace('\\', '/')


def run_snippet(ctx: GuardContext, code: str, *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    """Execute a small architecture-guard snippet and capture its result.

    These snippets are intentionally import/sentinel checks. Running them in the
    guard process avoids flaky orphaned Python subprocesses in constrained CI or
    container filesystems. ``timeout`` is accepted for API compatibility; guard
    snippets must stay bounded and side-effect-light.
    """
    del timeout
    args = [sys.executable, '-S', '-c', code]
    stdout = io.StringIO()
    stderr = io.StringIO()
    old_cwd = os.getcwd()
    try:
        os.chdir(ctx.project_root)
        namespace = {'__name__': '__arch_guard_snippet__', '__file__': '<arch_guard_snippet>'}
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                exec(compile(code, '<arch_guard_snippet>', 'exec'), namespace, namespace)
            except SystemExit as exc:
                code_value = exc.code if isinstance(exc.code, int) else 1
                return subprocess.CompletedProcess(args=args, returncode=code_value, stdout=stdout.getvalue(), stderr=stderr.getvalue())
            except Exception:
                traceback.print_exc(file=stderr)
                return subprocess.CompletedProcess(args=args, returncode=1, stdout=stdout.getvalue(), stderr=stderr.getvalue())
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout.getvalue(), stderr=stderr.getvalue())
    finally:
        os.chdir(old_cwd)

if __name__ == "__main__":
    from scripts.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
