from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol


SuccessCallback = Callable[[Any], None]
ErrorCallback = Callable[[Exception], None]


class ClosableBinding(Protocol):
    def close(self) -> None: ...


class TrimRawImageControllerPort(Protocol):
    def validate(self, path: str) -> str | None: ...

    def start(
        self,
        path: str,
        *,
        on_progress: Callable[[int], None],
        on_success: SuccessCallback,
        on_error: ErrorCallback,
    ) -> None: ...


class MagiskPatchControllerPort(Protocol):
    def get_arches(self, apk_path: str) -> list[str]: ...

    def validate(
        self, *, boot_file_path: str, magisk_apk_path: str
    ) -> tuple[bool, str | None]: ...

    def start(
        self,
        *,
        boot_file_path: str,
        magisk_apk_path: str,
        is_64bit: bool,
        keep_verity: bool,
        keep_force_encrypt: bool,
        recovery_mode: bool,
        arch: str,
        on_success: SuccessCallback,
        on_error: ErrorCallback,
    ) -> None: ...


class ByteCalculatorControllerPort(Protocol):
    def convert_value(self, text: str, origin_unit: str, target_unit: str) -> str: ...


class SelinuxAuditAllowControllerPort(Protocol):
    def validate(self, *, log_path: str, output_dir: str) -> str | None: ...

    def start(
        self,
        *,
        log_path: str,
        output_dir: str,
        on_success: SuccessCallback,
        on_error: ErrorCallback,
    ) -> None: ...


class GetFileInfoControllerPort(Protocol):
    def normalize_file(self, file_list: list[object]) -> str: ...

    def read_info(self, path: str) -> Any: ...


class StdoutRedirectControllerPort(Protocol):
    @property
    def data(self) -> Any: ...

    def write(self, value: object) -> None: ...

    def request_error_popup(self) -> bool: ...

    def consume_error_popup(self) -> str: ...


class MtkPortProfileProtocol(Protocol):
    name: str
    flags: Mapping[str, bool]


class MtkPortResultProtocol(Protocol):
    output_directory: object


class MtkPortControllerPort(Protocol):
    def profiles(self) -> tuple[MtkPortProfileProtocol, ...]: ...

    def start(
        self,
        *,
        profile_name: str,
        boot_image: str,
        system_image: str,
        port_rom: str,
        enabled_flags: Mapping[str, bool],
        output_as_image: bool,
        patch_magisk: bool,
        magisk_apk: str | None,
        target_arch: str,
        on_success: Callable[[MtkPortResultProtocol], None],
        on_error: ErrorCallback,
        on_finally: Callable[[], None] | None = None,
    ) -> None: ...


class FstabPatchControllerPort(Protocol):
    def start_scan(
        self, *, on_success: SuccessCallback, on_error: ErrorCallback
    ) -> None: ...

    def start_patch(
        self,
        partitions: Sequence[Any],
        selected_partitions: Sequence[str],
        *,
        on_success: Callable[[int], None],
        on_error: ErrorCallback,
    ) -> None: ...


class ReleaseCheckViewProtocol(Protocol):
    has_update: bool
    new_version: str | None
    body: str


class ReleaseAssetSelectionViewProtocol(Protocol):
    found: bool


class UpdateCheckOutcomePort(Protocol):
    release: ReleaseCheckViewProtocol
    selection: ReleaseAssetSelectionViewProtocol


class UpdateApplyResultViewProtocol(Protocol):
    success: bool
    warning_paths: Sequence[str]


class UpdateCleanupResultViewProtocol(Protocol):
    failed_paths: Sequence[str]


class PendingUpdateOutcomePort(Protocol):
    mode: str
    result: UpdateApplyResultViewProtocol | UpdateCleanupResultViewProtocol


class UpdateWorkflowPort(Protocol):
    def request_check(
        self, *, on_success: SuccessCallback, on_error: ErrorCallback
    ) -> None: ...

    def request_install(
        self,
        *,
        on_progress: Callable[[int], None],
        is_cancelled: Callable[[], bool],
        on_success: Callable[[object | None], None],
        on_error: ErrorCallback,
    ) -> None: ...

    def persist_and_launch(self, payload: object) -> None: ...

    def request_pending(
        self, *, on_success: SuccessCallback, on_error: ErrorCallback
    ) -> None: ...

    def recover_pending_failure(self) -> None: ...


class DebuggerControllerPort(Protocol):
    def build_info_text(self) -> str: ...

    def setting_keys(self) -> tuple[str, ...]: ...

    def read_setting(self, key: str) -> str: ...

    def write_setting(self, key: str, value: str) -> str: ...

    def global_keys(self) -> tuple[str, ...]: ...

    def read_global(self, key: str) -> str: ...

    def write_global(self, key: str, value: str) -> str: ...


class SettingsServicePort(Protocol):
    def set_theme(self, theme_id: str) -> None: ...

    def set_language(self, language_name: str) -> bool: ...

    def set_work_path(self, folder: str) -> None: ...

    def set_toggle(self, key: str, value: str | bool) -> str: ...

    def set_auto_update(self, value: str | bool) -> None: ...

    def set_error_helper_confidence(self, value: str | int | float) -> str: ...


class SplitSuperResultProtocol(Protocol):
    output_paths: Sequence[Path]


class SplitSuperControllerPort(Protocol):
    def suggest_output_directory(self, input_path: str) -> str: ...

    def validate(
        self,
        *,
        input_path: str,
        output_directory: str,
        part_count: int,
        block_size: int,
        suffix_format: str,
        keep_existing: bool,
    ) -> None: ...

    def start(
        self,
        *,
        input_path: str,
        output_directory: str,
        part_count: int,
        block_size: int,
        suffix_format: str,
        keep_existing: bool,
        on_progress: Callable[[int], None],
        on_success: Callable[[SplitSuperResultProtocol], None],
        on_error: ErrorCallback,
        on_finally: Callable[[], None],
    ) -> None: ...


class MergeSuperContextPort(Protocol):
    can_run: bool
    project_path: Path | None
    output_path: Path | None


class MergeSuperResultProtocol(Protocol):
    status: object
    output_path: object | None


class MergeSuperControllerPort(Protocol):
    def context(self) -> MergeSuperContextPort: ...

    def start(
        self,
        *,
        output_name: str,
        delete_source: bool,
        on_progress: Callable[[int], None],
        on_success: Callable[[MergeSuperResultProtocol], None],
        on_error: ErrorCallback,
        on_finally: Callable[[], None],
    ) -> None: ...


class DecryptXtcXmlControllerPort(Protocol):
    def validate(self, path: str) -> str | None: ...

    def start(
        self, path: str, *, on_success: SuccessCallback, on_error: ErrorCallback
    ) -> None: ...


class MergeQualcommControllerPort(Protocol):
    def validate(
        self, *, rawprogram_xml: str, partition_name: str, output_path: str
    ) -> str | None: ...

    def start(
        self,
        *,
        rawprogram_xml: str,
        partition_name: str,
        output_path: str,
        on_success: SuccessCallback,
        on_error: ErrorCallback,
    ) -> None: ...


class PostInstallEntryProtocol(Protocol):
    partition: str
    run_postinstall: bool
    postinstall_path: str
    filesystem_type: str
    postinstall_optional: bool


class PostInstallConfigControllerPort(Protocol):
    def load(self) -> dict[str, PostInstallEntryProtocol]: ...

    def normalize_partition_name(self, partition: str) -> str: ...

    def create_entry(
        self,
        partition: str,
        *,
        run_postinstall: bool = False,
        postinstall_path: str = "",
        filesystem_type: str = "",
        postinstall_optional: bool = False,
    ) -> PostInstallEntryProtocol: ...

    def save(self, entries: Iterable[PostInstallEntryProtocol]) -> None: ...


__all__ = [
    "ByteCalculatorControllerPort",
    "ClosableBinding",
    "DebuggerControllerPort",
    "DecryptXtcXmlControllerPort",
    "FstabPatchControllerPort",
    "GetFileInfoControllerPort",
    "MagiskPatchControllerPort",
    "MergeQualcommControllerPort",
    "MergeSuperContextPort",
    "MergeSuperControllerPort",
    "MtkPortControllerPort",
    "PendingUpdateOutcomePort",
    "PostInstallConfigControllerPort",
    "SelinuxAuditAllowControllerPort",
    "SettingsServicePort",
    "StdoutRedirectControllerPort",
    "TrimRawImageControllerPort",
    "UpdateApplyResultViewProtocol",
    "UpdateCheckOutcomePort",
    "UpdateCleanupResultViewProtocol",
    "UpdateWorkflowPort",
]
