from __future__ import annotations

from typing import Protocol

from src.ui.common.byte_size import format_localized_binary_byte_size
from src.ui.common.technical_choices import technical_label
from src.ui.localization import LocalizationCatalog
from src.ui.tabs.project.pack.super import keys


class PackableSuperImageProtocol(Protocol):
    name: str
    image_type: str


class PackSuperResultProtocol(Protocol):
    output_is_sparse: bool
    output_path: object
    output_logical_size: int
    output_physical_size: int
    requested_device_size: int
    report_path: object


def format_packable_super_image(
    entry: PackableSuperImageProtocol,
    *,
    texts: LocalizationCatalog,
) -> str:
    return f"{entry.name} [{technical_label(texts, entry.image_type)}]"


def apply_initial_super_state(view, state) -> None:
    if state.block_device_name:
        view.block_device_name.set(state.block_device_name)
    if isinstance(state.super_size, int):
        view.super_size.set(state.super_size)
    if state.group_name:
        view.group_name.set(view._display_group_name(state.group_name))
    if isinstance(state.super_type, int):
        view.super_type.set(state.super_type)
    view.selected = list(state.selected)


def render_packable_super_entries(view, entries) -> None:
    view.tl.clear()
    for entry in entries:
        view.tl.insert(
            format_packable_super_image(entry, texts=view._texts),
            entry.name,
            entry.selected,
            refresh=False,
        )
    view.tl.update_ui()


def describe_pack_super_result(
    result: PackSuperResultProtocol,
    *,
    texts: LocalizationCatalog,
) -> str:
    output_format = texts.resolve_required_ui_text(
        keys.RESULT_ANDROID_SPARSE_FORMAT_NAME
        if result.output_is_sparse
        else keys.RESULT_RAW_FORMAT_NAME
    )
    return "\n".join(
        (
            texts.resolve_required_ui_text(keys.RESULT_OUTPUT_FORMAT).format(
                path=result.output_path
            ),
            texts.resolve_required_ui_text(keys.RESULT_FORMAT_FORMAT).format(
                format=output_format
            ),
            texts.resolve_required_ui_text(keys.RESULT_LOGICAL_SIZE_FORMAT).format(
                human_size=format_localized_binary_byte_size(
                    result.output_logical_size, texts=texts
                ),
                byte_size=result.output_logical_size,
            ),
            texts.resolve_required_ui_text(keys.RESULT_PHYSICAL_SIZE_FORMAT).format(
                human_size=format_localized_binary_byte_size(
                    result.output_physical_size, texts=texts
                ),
                byte_size=result.output_physical_size,
            ),
            texts.resolve_required_ui_text(
                keys.RESULT_REQUESTED_DEVICE_SIZE_FORMAT
            ).format(
                human_size=format_localized_binary_byte_size(
                    result.requested_device_size, texts=texts
                ),
                byte_size=result.requested_device_size,
            ),
            texts.resolve_required_ui_text(keys.RESULT_REPORT_FORMAT).format(
                path=result.report_path
            ),
        )
    )


__all__ = [
    "PackSuperResultProtocol",
    "PackableSuperImageProtocol",
    "apply_initial_super_state",
    "describe_pack_super_result",
    "format_packable_super_image",
    "render_packable_super_entries",
]
