from __future__ import annotations

from dataclasses import dataclass

from src.app.runtime.contexts.contracts import AnimationProtocol, HostWindowProtocol, SettingsProtocol, StateBagProtocol, VariableProtocol
from src.app.runtime.contexts.ui import resolve_language, resolve_theme, resolve_ui_host_window


@dataclass(frozen=True)
class SettingsManagerDefaults:
    animation: AnimationProtocol | object
    language_var: VariableProtocol | object
    theme_var: VariableProtocol | object
    states: StateBagProtocol | object
    window: HostWindowProtocol | object



def resolve_settings(settings: SettingsProtocol | None = None):
    if settings is not None:
        return settings
    from src.app.runtime.core_access import require_settings
    return require_settings()



def resolve_settings_optional(settings=None):
    if settings is not None:
        return settings
    from src.app.runtime.core_access import get_settings
    return get_settings()



def resolve_states(states=None):
    if states is not None:
        return states
    from src.app.runtime.defaults_access import require_states
    return require_states()



def resolve_states_optional(states=None):
    if states is not None:
        return states
    from src.app.runtime.defaults_access import get_states
    return get_states()



def resolve_animation(animation: AnimationProtocol | None = None):
    if animation is not None:
        return animation
    from src.app.runtime.window_access import require_animation
    return require_animation()



def resolve_settings_manager_defaults(*, animation=None, language_var=None, theme_var=None, states=None, window=None) -> SettingsManagerDefaults:
    if animation is None or language_var is None or theme_var is None or states is None or window is None:
        animation = resolve_animation(animation)
        language_var = resolve_language(language_var)
        theme_var = resolve_theme(theme_var)
        states = resolve_states(states)
        window = resolve_ui_host_window(window)
    return SettingsManagerDefaults(animation=animation, language_var=language_var, theme_var=theme_var, states=states, window=window)


__all__ = [
    'SettingsManagerDefaults',
    'resolve_animation',
    'resolve_settings',
    'resolve_settings_manager_defaults',
    'resolve_settings_optional',
    'resolve_states',
    'resolve_states_optional',
]
