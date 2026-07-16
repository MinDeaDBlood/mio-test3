from __future__ import annotations

from dataclasses import replace

from src.core.json_store import JsonEdit
from src.logic.projects.pack.partition_flow import (
    build_default_pack_partition_dependencies,
    has_packable_partitions,
    load_parts_dict,
    Ext4SizeMode,
    PackPartitionRequest,
    pack_selected_partitions,
)
from src.logic.projects.pack.partition_size import resolve_configured_ext4_size


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(
    value: object,
    *,
    error_key: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    try:
        resolved = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(error_key) from exc
    if minimum is not None and resolved < minimum:
        raise ValueError(error_key)
    if maximum is not None and resolved > maximum:
        raise ValueError(error_key)
    return resolved


def _as_ext4_size_mode(value: object) -> Ext4SizeMode:
    normalized = str(value).strip().lower()
    if normalized == Ext4SizeMode.FIXED.value:
        return Ext4SizeMode.FIXED
    return Ext4SizeMode.AUTO


class PartitionPackController:
    """Application controller for the partition-packing workflow."""

    def __init__(self, *, runtime, animation):
        self.runtime = runtime
        self.animation = animation
        self.dependencies = build_default_pack_partition_dependencies()
        self._packing_hook_sent = False

    def requires_configuration(self, chosen_parts: list[str]) -> bool:
        parts_dict = load_parts_dict(self.runtime.workflow.work_path, JsonEdit)
        return has_packable_partitions(chosen_parts, parts_dict)

    def notify_before_pack(self) -> None:
        manager = self.runtime.module_manager
        manager.addon_loader.run_entry(manager.addon_entries.before_pack)

    def notify_packing_start(self) -> None:
        if self._packing_hook_sent:
            return
        self._packing_hook_sent = True
        manager = self.runtime.module_manager
        manager.addon_loader.run_entry(manager.addon_entries.packing)

    def project_exists(self) -> bool:
        return self.runtime.workflow.project_selected

    def current_work_path(self) -> str:
        return self.runtime.workflow.work_path

    def load_fixed_sizes(
        self,
        *,
        chosen_parts: list[str],
        custom_size: dict[str, int | str],
    ) -> dict[str, int | str]:
        result = dict(custom_size)
        work = self.current_work_path()
        for partition_name in chosen_parts:
            if result.get(partition_name, "") not in ("", None):
                continue
            result[partition_name] = resolve_configured_ext4_size(
                work,
                partition_name,
                None,
                prefer_dynamic_resize=True,
            )
        return result

    def _build_request(self, form: dict[str, object]) -> PackPartitionRequest:
        return PackPartitionRequest(
            chosen_parts=list(form.get("chosen_parts") or []),
            patch_vbmeta=_as_bool(form.get("patch_vbmeta")),
            remove_source_files=_as_bool(form.get("remove_source_files")),
            ext4_packer=str(form.get("ext4_packer") or "make_ext4fs"),
            ext4_size_mode=_as_ext4_size_mode(form.get("ext4_size_mode")),
            output_format=str(form.get("output_format") or "raw"),
            erofs_compress_format=str(form.get("erofs_compress_format") or "lz4hc"),
            erofs_level=_as_int(
                form.get("erofs_level", 0),
                error_key="pack_partition_erofs_level_invalid",
                minimum=0,
                maximum=9,
            ),
            brotli_level=_as_int(
                form.get("brotli_level", 0),
                error_key="pack_partition_brotli_level_invalid",
                minimum=0,
                maximum=9,
            ),
            utc=_as_int(
                form.get("utc", 0), error_key="pack_partition_utc_invalid", minimum=0
            ),
            origin_fs=str(form.get("origin_fs") or "ext"),
            modify_fs=str(form.get("modify_fs") or "ext"),
            fs_convert=_as_bool(form.get("fs_convert")),
            erofs_old_kernel=_as_bool(form.get("erofs_old_kernel")),
            custom_size=dict(form.get("custom_size") or {}),
        )

    def prepare_request(self, request):
        if request.ext4_size_mode is not Ext4SizeMode.FIXED:
            return request
        fixed_sizes = self.load_fixed_sizes(
            chosen_parts=request.chosen_parts,
            custom_size=dict(request.custom_size),
        )
        return replace(request, custom_size=fixed_sizes)

    def validate_form(self, form: dict[str, object]) -> None:
        self._build_request(form)

    def execute_form(self, form: dict[str, object]) -> bool | None:
        if not self.project_exists():
            return False
        request = self._build_request(form)
        self.notify_packing_start()
        prepared_request = self.prepare_request(request)
        return pack_selected_partitions(
            prepared_request, self.runtime.workflow, self.dependencies
        )

    def execute_background(self, form: dict[str, object]) -> None:
        self.animation(self.execute_form)(dict(form))


__all__ = ["PartitionPackController"]
