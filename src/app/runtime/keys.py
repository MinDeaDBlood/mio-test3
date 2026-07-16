from __future__ import annotations

EARLY_RUNTIME_KEYS = frozenset(
    {
        'prog_path',
        'tool_self',
        'temp',
        'log_dir',
        'tool_log',
        'context_rule_file',
        'states',
        'call',
        'module_exec',
    }
)
CORE_RUNTIME_KEYS = frozenset(
    {
        'settings',
        'module_error_codes',
        'module_manager',
        'project_manager',
    }
)
BOOTSTRAP_WINDOW_KEYS = frozenset(
    {
        'main_window',
        'animation',
        'ui_scheduler',
        'current_project_name',
        'theme',
        'language',
    }
)
BOOTSTRAP_UI_KEYS = frozenset({'unpack_view', 'project_menu'})
ALL_RUNTIME_KEYS = frozenset(
    {
        *EARLY_RUNTIME_KEYS,
        *CORE_RUNTIME_KEYS,
        *BOOTSTRAP_WINDOW_KEYS,
        *BOOTSTRAP_UI_KEYS,
    }
)

__all__ = [
    'ALL_RUNTIME_KEYS',
    'BOOTSTRAP_UI_KEYS',
    'BOOTSTRAP_WINDOW_KEYS',
    'CORE_RUNTIME_KEYS',
    'EARLY_RUNTIME_KEYS',
]
