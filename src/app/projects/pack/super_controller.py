from __future__ import annotations

import logging

from src.logic.projects.pack.super.planning import (
    generate_super_dynamic_list,
    load_pack_super_initial_state,
    scan_packable_super_images,
    validate_super_size,
)
from src.logic.projects.pack.super.service import pack_super


class SuperPackController:
    """Application controller for super image planning and packing."""

    def __init__(self, *, runtime, window_task_runner, host_task_runner, logger=None):
        self.runtime = runtime
        self.window_task_runner = window_task_runner
        self.host_task_runner = host_task_runner
        self.logger = logger or logging

    @property
    def work_path(self) -> str:
        return self.runtime.work_path

    def project_exists(self) -> bool:
        return self.runtime.project_manager.exist()

    def load_initial_state(self):
        return load_pack_super_initial_state(self.work_path)

    def scan_images(self, selected):
        return scan_packable_super_images(self.work_path, selected)

    def validate_size(self, selected, size: int):
        return validate_super_size(self.work_path, selected, size)

    def generate_dynamic_list(
        self,
        *,
        group_name: str,
        size: int,
        super_type: int,
        part_list: list[str],
        on_error,
        on_finally,
    ) -> None:
        self.window_task_runner.run(
            generate_super_dynamic_list,
            worker_kwargs={
                'group_name': group_name,
                'size': size,
                'super_type': super_type,
                'part_list': part_list,
                'work': self.runtime.project_manager.current_work_path(),
            },
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )

    def start_pack(
        self,
        *,
        sparse: bool,
        group_name: str,
        size: int,
        super_type: int,
        part_list: list[str],
        del_: bool,
        attrib: str,
        block_device_name: str,
        on_success,
        on_error,
        on_finally,
    ) -> None:
        request = {
            'sparse': sparse,
            'group_name': group_name,
            'size': size,
            'super_type': super_type,
            'part_list': list(part_list),
            'del_': del_,
            'attrib': attrib,
            'block_device_name': block_device_name,
            'work': self.work_path,
            'output_dir': self.runtime.project_manager.current_work_output_path(),
            'return_result': True,
        }
        self.host_task_runner.run(
            pack_super,
            worker_kwargs=request,
            on_success=on_success,
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )



__all__ = ['SuperPackController']
