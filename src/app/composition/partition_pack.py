from __future__ import annotations

from src.app.localization_runtime import lang
from src.app.projects.pack.partition_controller import PartitionPackController
from src.app.projects.pack.partition_runtime import build_pack_partition_runtime, resolve_pack_partition_host_window
from src.app.runtime.contexts.settings import resolve_animation
from src.app.ui_feedback import build_ui_notifier
from src.app.composition.service_output import build_ui_service_output
from src.ui.tabs.project.pack.partition.window import PackPartition


def open_partition_pack(parts: list[str]):
    host_window = resolve_pack_partition_host_window()
    notifier = build_ui_notifier(host_window=host_window)
    runtime = build_pack_partition_runtime(output=build_ui_service_output(texts=lang, notify=notifier.show))
    controller = PartitionPackController(runtime=runtime, animation=resolve_animation())
    return PackPartition(
        parts,
        texts=lang,
        controller=controller,
        host_window=host_window,
        auto_start=not controller.requires_configuration(parts),
    )


__all__ = ['open_partition_pack']
