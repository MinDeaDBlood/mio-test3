from __future__ import annotations

from dataclasses import replace
import logging

from src.logic.projects.pack.partition_flow import (
    Ext4SizeMode,
    PackPartitionRequest,
    build_default_pack_partition_dependencies,
    pack_selected_partitions,
)
from src.logic.projects.pack.partition_size import resolve_configured_ext4_size
from src.platform.operation_logging import operation_context

logger = logging.getLogger(__name__)


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
    """Application controller for the partition packing workflow."""

    def __init__(self, *, runtime, animation):
        self.runtime = runtime
        self.animation = animation
        self.dependencies = build_default_pack_partition_dependencies()
        self._before_pack_hook_sent = False
        self._packing_hook_sent = False

    def notify_before_pack(self) -> None:
        if self._before_pack_hook_sent:
            logger.debug("partition_pack.plugin_hook: entry=before_pack state=already_sent")
            return
        self.runtime.plugin_lifecycle.before_pack()
        self._before_pack_hook_sent = True

    def notify_packing_start(self) -> None:
        if self._packing_hook_sent:
            logger.debug("partition_pack.plugin_hook: entry=packing state=already_sent")
            return
        self._packing_hook_sent = True
        self.runtime.plugin_lifecycle.packing_started()

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
        logger.debug(
            "partition_pack.fixed_sizes_load: work=%s selected=%r existing=%r",
            work,
            chosen_parts,
            sorted(result),
        )
        for partition_name in chosen_parts:
            if result.get(partition_name, "") not in ("", None):
                continue
            result[partition_name] = resolve_configured_ext4_size(
                work,
                partition_name,
                None,
                prefer_dynamic_resize=True,
            )
            logger.debug(
                "partition_pack.fixed_size_resolved: partition=%s size=%s",
                partition_name,
                result[partition_name],
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

    def prepare_request(self, request: PackPartitionRequest) -> PackPartitionRequest:
        if request.ext4_size_mode is not Ext4SizeMode.FIXED:
            return request
        fixed_sizes = self.load_fixed_sizes(
            chosen_parts=request.chosen_parts,
            custom_size=dict(request.custom_size),
        )
        return replace(request, custom_size=fixed_sizes)

    def validate_form(self, form: dict[str, object]) -> None:
        request = self._build_request(form)
        logger.debug(
            "partition_pack.form_validated: selected=%r output_format=%s ext4_packer=%s",
            request.chosen_parts,
            request.output_format,
            request.ext4_packer,
        )

    def execute_form(self, form: dict[str, object]) -> bool | None:
        if not self.project_exists():
            logger.warning("partition_pack.rejected: reason=project_not_selected")
            return False
        request = self._build_request(form)
        with operation_context(
            "project.partition_pack",
            partitions=request.chosen_parts,
            output_format=request.output_format,
            fs_convert=request.fs_convert,
        ):
            logger.info(
                "partition_pack.request: selected=%r patch_vbmeta=%s "
                "remove_source_files=%s ext4_packer=%s ext4_size_mode=%s "
                "output_format=%s erofs_format=%s erofs_level=%s "
                "brotli_level=%s utc=%s fs_convert=%s origin_fs=%s "
                "modify_fs=%s erofs_old_kernel=%s custom_size_keys=%r "
                "work=%s output=%s",
                request.chosen_parts,
                request.patch_vbmeta,
                request.remove_source_files,
                request.ext4_packer,
                request.ext4_size_mode.value,
                request.output_format,
                request.erofs_compress_format,
                request.erofs_level,
                request.brotli_level,
                request.utc,
                request.fs_convert,
                request.origin_fs,
                request.modify_fs,
                request.erofs_old_kernel,
                sorted(request.custom_size),
                self.runtime.workflow.work_path,
                self.runtime.workflow.output_path,
            )
            self.notify_before_pack()
            self.notify_packing_start()
            prepared_request = self.prepare_request(request)
            result = pack_selected_partitions(
                prepared_request, self.runtime.workflow, self.dependencies
            )
            logger.info(
                "partition_pack.result: success=%s selected=%r output=%s",
                result,
                prepared_request.chosen_parts,
                self.runtime.workflow.output_path,
            )
            return result

    def execute_background(self, form: dict[str, object]) -> None:
        logger.info(
            "partition_pack.background_scheduled: selected=%r",
            list(form.get("chosen_parts") or []),
        )
        self.animation(self.execute_form)(dict(form))


__all__ = ["PartitionPackController"]
