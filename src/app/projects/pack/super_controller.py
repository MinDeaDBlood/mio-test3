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

    @property
    def source_paths(self) -> tuple[str, ...]:
        paths = [self.work_path]
        input_path = self.runtime.input_path
        if input_path and input_path not in paths:
            paths.append(input_path)
        return tuple(paths)

    def project_exists(self) -> bool:
        return self.runtime.project_manager.exist()

    def load_initial_state(self):
        return load_pack_super_initial_state(self.runtime.metadata_path)

    def scan_images(self, selected):
        return scan_packable_super_images(self.source_paths, selected)

    def validate_size(self, selected, size: int):
        return validate_super_size(self.source_paths, selected, size)

    def load_initial_data(self):
        state = self.load_initial_state()
        entries = scan_packable_super_images(self.source_paths, state.selected)
        return state, entries

    def request_initial_data(self, *, on_success, on_error) -> None:
        self.window_task_runner.run(
            self.load_initial_data,
            on_success=on_success,
            on_error=on_error,
        )

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
                'work': self.work_path,
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
        fallback_sources = list(self.source_paths[1:])
        if fallback_sources:
            request['source_dirs'] = fallback_sources
        self.host_task_runner.run(
            pack_super,
            worker_kwargs=request,
            on_success=on_success,
            on_error=on_error,
            on_finally=on_finally,
            exclusive=True,
        )



__all__ = ['SuperPackController']
