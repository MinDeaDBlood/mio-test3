from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol, TypeVar, runtime_checkable

from src.logic.plugins.uninstall.result import PluginUninstallResult


@runtime_checkable
class MessagePopProtocol(Protocol):
    def __call__(
        self,
        text: str = '',
        color: str = 'red',
        title: str | None = None,
        master: object | None = None,
    ) -> object: ...


@runtime_checkable
class SchedulerHostProtocol(Protocol):
    def after(self, delay_ms: int, callback: Callable[..., object], *args: object) -> str: ...
    def after_cancel(self, after_id: str) -> None: ...
    def winfo_exists(self) -> bool: ...
    def winfo_toplevel(self) -> 'SchedulerHostProtocol': ...



@runtime_checkable
class PresenceWindowProtocol(Protocol):
    def winfo_exists(self) -> bool: ...
    def lift(self) -> object: ...
    def focus_force(self) -> object: ...

@runtime_checkable
class HostWindowProtocol(SchedulerHostProtocol, Protocol):
    message_pop: MessagePopProtocol


@runtime_checkable
class SettingsProtocol(Protocol):
    plugin_repo: str | None
    error_helper_enabled: str
    error_helper_confidence: str
    language: str
    theme: str
    active_code: str
    path: str | None

    def load(self) -> object: ...
    def set_value(self, name: str, value: object) -> object: ...


@runtime_checkable
class StateBagProtocol(Protocol):
    active_mpk_store_instance: PresenceWindowProtocol | None
    mpk_store: bool
    in_oobe: bool
    debugger_window: bool
    update_window: bool
    run_source: bool
    open_pids: list[int]
    open_source_license: str




class ModuleErrorCodesProtocol(Protocol):
    Normal: object
    ArchNotSupported: object
    PlatformNotSupport: object
    DependsMissing: object
    IsBroken: object


@runtime_checkable
class ModuleManagerProtocol(Protocol):
    module_dir: str

    def request_plugin_list_refresh(self) -> bool: ...
    def install(self, mpk_path: str) -> tuple[object, str]: ...
    def uninstall_plugin(
        self,
        plugin_id: str,
        *,
        include_dependents: bool = True,
    ) -> PluginUninstallResult: ...
    def check_mpk(self, mpk: str) -> tuple[object, str]: ...
    def claim_background_load(self) -> bool: ...
    def load_plugins_and_notify(self) -> None: ...
    def is_installed(self, plugin_id: str) -> bool: ...
    def export(self, plugin_id: str, *, output_dir: str) -> int | None: ...
    def create_plugin_scaffold(self, data: Mapping[str, object]) -> str: ...
    def run(self, plugin_id: str | None = None, *, runtime: object) -> int: ...


@runtime_checkable
class ProjectManagerProtocol(Protocol):
    def current_input_path(self) -> str: ...
    def current_unpack_path(self) -> str: ...
    def current_work_path(self) -> str: ...
    def current_work_output_path(self) -> str: ...
    def exist(self, name: str | None = None) -> bool: ...


@runtime_checkable
class ProjectMenuProtocol(Protocol):
    def listdir(self) -> object: ...
    def set_project(self, name: str) -> object: ...
    def remove(self) -> object: ...


@runtime_checkable
class UnpackViewProtocol(Protocol):
    def refs(self, auto: bool = False) -> object: ...


@runtime_checkable
class VariableProtocol(Protocol):
    def get(self) -> object: ...
    def set(self, value: object) -> object: ...


@runtime_checkable
class AnimationProtocol(Protocol):
    master: object

    def run(self) -> object: ...
    def stop(self) -> object: ...
    def init(self) -> object: ...
    def has_tasks(self) -> bool: ...
    def load_gif(self, gif: object) -> object: ...


@runtime_checkable
class UiSchedulerProtocol(Protocol):
    def post(
        self,
        callback: Callable[..., object],
        args: tuple[object, ...] = (),
    ) -> bool: ...
    def start(self) -> bool: ...
    def stop(self) -> bool: ...


TaskResult = TypeVar('TaskResult')


@runtime_checkable
class UiTaskRunnerProtocol(Protocol):
    def run(
        self,
        worker: Callable[..., TaskResult],
        *args: object,
        on_success: Callable[[TaskResult], object] | None = None,
        on_error: Callable[[Exception], object] | None = None,
        on_finally: Callable[[], object] | None = None,
        daemon: bool = True,
    ) -> None: ...
    def fire_and_forget(
        self,
        worker: Callable[..., object],
        *args: object,
        daemon: bool = True,
    ) -> None: ...


__all__ = [
    'AnimationProtocol',
    'HostWindowProtocol',
    'MessagePopProtocol',
    'ModuleErrorCodesProtocol',
    'PresenceWindowProtocol',
    'ModuleManagerProtocol',
    'ProjectManagerProtocol',
    'ProjectMenuProtocol',
    'SchedulerHostProtocol',
    'SettingsProtocol',
    'StateBagProtocol',
    'UnpackViewProtocol',
    'UiSchedulerProtocol',
    'UiTaskRunnerProtocol',
    'VariableProtocol',
]
