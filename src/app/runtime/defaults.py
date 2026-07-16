"""Authoritative runtime defaults for early startup.

These values exist before the Tk main window is constructed and used to live in
``src.ui.shared_state``. They now belong to the application layer so startup
contracts remain explicit and non-UI code can rely on a single source of truth.
"""

from __future__ import annotations

import os
import sys
import time
from functools import lru_cache
from typing import Any

from src.app.runtime.contract import EARLY_RUNTIME_DEFAULT_KEYS, validate_runtime_keys
from src.platform.runtime_paths import CONTEXT_RULES_FILE, TEMP_DIR
from src.app.runtime.models import EarlyRuntimeDefaults
from src.core.process_runner import call
from src.core.paths import prog_path
from src.app.runtime.flags import states
from src.core.random_utils import v_code


RUNTIME_DEFAULTS: dict[str, Any]
context_rule_file: str
log_dir: str
module_exec: str
temp: str
tool_log: str
tool_self: str


@lru_cache(maxsize=1)
def get_early_runtime_defaults() -> EarlyRuntimeDefaults:
    tool_self = os.path.normpath(os.path.abspath(sys.argv[0]))
    temp = str(TEMP_DIR).replace(os.sep, "/")
    log_dir = os.path.join(prog_path, "logs").replace(os.sep, "/")
    tool_log = (
        f"{log_dir}/{time.strftime('%Y%m%d_%H-%M-%S', time.localtime())}_{v_code()}.log"
    )
    context_rule_file = str(CONTEXT_RULES_FILE)
    module_exec = os.path.join(prog_path, "bin", "exec.sh").replace(os.sep, "/")
    return EarlyRuntimeDefaults(
        prog_path=prog_path,
        tool_self=tool_self,
        temp=temp,
        log_dir=log_dir,
        tool_log=tool_log,
        context_rule_file=context_rule_file,
        states=states,
        call=call,
        module_exec=module_exec,
    )


def export_runtime_defaults() -> dict[str, Any]:
    """Return a copy of the startup runtime defaults."""
    return get_early_runtime_defaults().export_runtime_values()


def get_runtime_default(name: str, default: Any = None) -> Any:
    return export_runtime_defaults().get(name, default)


def register_runtime_defaults(
    defaults: EarlyRuntimeDefaults | None = None,
) -> dict[str, Any]:
    """Register the early-startup runtime defaults explicitly.

    This keeps startup deterministic without relying on import-time mutation of
    ``runtime_state``.
    """
    from src.app.runtime.phases import register_early_runtime_defaults

    active_defaults = get_early_runtime_defaults() if defaults is None else defaults
    registered = register_early_runtime_defaults(
        **active_defaults.export_runtime_values()
    )
    validate_runtime_keys(
        EARLY_RUNTIME_DEFAULT_KEYS,
        runtime_values=registered,
        context="early runtime defaults",
    )
    return registered


def __getattr__(name: str):
    if name == "RUNTIME_DEFAULTS":
        return export_runtime_defaults()
    if name in {
        "tool_self",
        "temp",
        "log_dir",
        "tool_log",
        "context_rule_file",
        "module_exec",
    }:
        return getattr(get_early_runtime_defaults(), name)
    raise AttributeError(name)


__all__ = [
    "EarlyRuntimeDefaults",
    "RUNTIME_DEFAULTS",
    "call",
    "context_rule_file",
    "export_runtime_defaults",
    "get_early_runtime_defaults",
    "get_runtime_default",
    "log_dir",
    "module_exec",
    "prog_path",
    "register_runtime_defaults",
    "states",
    "temp",
    "tool_log",
    "tool_self",
]
