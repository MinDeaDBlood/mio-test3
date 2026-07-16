from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageSizeInfo:
    path: str
    logical_size: int
    physical_size: int
    sparse: bool


@dataclass(frozen=True)
class PartitionImageInfo:
    partition_name: str
    image_name: str
    image: ImageSizeInfo | None
    group_name: str
    attributes: str

    @property
    def partition_size(self) -> int:
        return 0 if self.image is None else self.image.logical_size


@dataclass(frozen=True)
class PackSuperResult:
    output_path: str
    report_path: str
    sparse: bool
    requested_device_size: int
    output_logical_size: int
    output_physical_size: int
    output_is_sparse: bool
    partitions: tuple[PartitionImageInfo, ...]

    def __bool__(self) -> bool:
        return bool(self.output_path)


__all__ = ['ImageSizeInfo', 'PackSuperResult', 'PartitionImageInfo']
