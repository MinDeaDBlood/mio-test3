from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from src.core.file_ops import remove_path
from src.core.merge_sparse import SparseMergeStatus, merge_sparse_segments
from src.logic.tools.merge_super.models import MergeSuperRequest, MergeSuperResult, MergeSuperStatus


class ProjectManagerPort(Protocol):
    def exist(self) -> bool: ...
    def current_work_path(self) -> str: ...
    def current_work_output_path(self) -> str: ...


MergeFunction = Callable[..., object]
ProgressCallback = Callable[[int], None]


class MergeSuperService:
    def __init__(
        self,
        *,
        project_manager: ProjectManagerPort,
        tool_bin_path: str,
        merge_function: MergeFunction = merge_sparse_segments,
    ) -> None:
        self._project_manager = project_manager
        self._tool_bin_path = tool_bin_path
        self._merge_function = merge_function

    def has_project(self) -> bool:
        return self._project_manager.exist()

    def current_project_path(self) -> Path:
        return Path(self._project_manager.current_work_path())

    def current_output_path(self) -> Path:
        return Path(self._project_manager.current_work_output_path())

    def execute(
        self,
        request: MergeSuperRequest,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> MergeSuperResult:
        if not self.has_project():
            return MergeSuperResult(status=MergeSuperStatus.NO_PROJECT)

        output_name = request.output_name.strip()
        if not output_name:
            raise ValueError('Output filename is required')
        if Path(output_name).name != output_name:
            raise ValueError('Output filename must not contain a directory path')

        core_result = self._merge_function(
            source_directory=self.current_project_path(),
            output_path=self.current_output_path() / output_name,
            tool_bin_path=self._tool_bin_path,
            progress_callback=progress_callback,
        )

        status_map = {
            SparseMergeStatus.MERGED: MergeSuperStatus.MERGED,
            SparseMergeStatus.NO_SEGMENTS: MergeSuperStatus.NO_SEGMENTS,
            SparseMergeStatus.OUTPUT_EXISTS: MergeSuperStatus.OUTPUT_EXISTS,
        }
        deleted_count = 0
        if core_result.status is SparseMergeStatus.MERGED and request.delete_source:
            for segment_path in core_result.segment_paths:
                remove_path(segment_path, missing_ok=False)
                deleted_count += 1

        return MergeSuperResult(
            status=status_map[core_result.status],
            output_path=core_result.output_path,
            segment_count=len(core_result.segment_paths),
            deleted_segment_count=deleted_count,
        )


__all__ = ['MergeSuperService', 'ProjectManagerPort']
