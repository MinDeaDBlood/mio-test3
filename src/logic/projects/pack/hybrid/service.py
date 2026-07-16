from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from src.core.file_types import gettype
from src.core.process_runner import call
from src.core.sparse_tools import simg2img

from .models import HybridImageOperation, HybridPackRequest, HybridPackResult


class HybridPackError(RuntimeError):
    pass


class PayloadProjectNotSupportedError(HybridPackError):
    pass


class HybridTemplateError(HybridPackError):
    pass


class HybridRomPackService:
    def __init__(
        self,
        *,
        process_call: Callable[..., int | None] = call,
        image_type_getter: Callable[[str], str] = gettype,
        sparse_converter: Callable[[str], object] = simg2img,
    ):
        self._process_call = process_call
        self._image_type_getter = image_type_getter
        self._sparse_converter = sparse_converter

    def pack(self, request: HybridPackRequest) -> HybridPackResult:
        output_dir = request.output_dir.resolve()
        template_dir = request.template_dir.resolve()
        if not output_dir.is_dir():
            raise HybridPackError(f'Project output directory does not exist: {output_dir}')
        if not template_dir.is_dir():
            raise HybridTemplateError(f'Hybrid template directory does not exist: {template_dir}')
        if not request.right_device.strip():
            raise HybridPackError('Target device name is empty')
        if request.compression_threshold < 0:
            raise HybridPackError('Compression threshold must not be negative')
        if (output_dir / 'payload.bin').exists():
            raise PayloadProjectNotSupportedError('Hybrid ZIP packing is not supported for payload.bin projects')

        images_dir = self._prepare_layout(output_dir, template_dir)
        self._write_right_device(output_dir, request.right_device.strip())
        script_path = output_dir / 'META-INF' / 'com' / 'google' / 'android' / 'update-binary'
        operations = self._process_images(output_dir, images_dir, request.compression_threshold)
        self._write_update_script(script_path, request.right_device.strip(), operations)
        return HybridPackResult(output_dir=output_dir, images_dir=images_dir, operations=tuple(operations))

    @staticmethod
    def _prepare_layout(output_dir: Path, template_dir: Path) -> Path:
        firmware_update_dir = output_dir / 'firmware-update'
        images_dir = output_dir / 'images'
        if firmware_update_dir.exists():
            if images_dir.exists():
                raise HybridPackError('Both firmware-update and images directories exist')
            firmware_update_dir.rename(images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)
        meta_inf = output_dir / 'META-INF'
        if meta_inf.exists():
            shutil.rmtree(meta_inf)
        shutil.copytree(template_dir, output_dir, dirs_exist_ok=True)
        return images_dir

    @staticmethod
    def _write_right_device(output_dir: Path, right_device: str) -> None:
        target = output_dir / 'bin' / 'right_device'
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('w', encoding='gbk', newline='\n') as stream:
            stream.write(f'{right_device}\n')

    def _process_images(self, output_dir: Path, images_dir: Path, threshold: int) -> list[HybridImageOperation]:
        operations: list[HybridImageOperation] = []
        for image_path in sorted(images_dir.glob('*.img')):
            operations.append(self._prepare_image(image_path, images_dir, threshold, move_to_images=False))
        for image_path in sorted(output_dir.glob('*.img')):
            if image_path.name.startswith('preloader_'):
                continue
            operations.append(self._prepare_image(image_path, images_dir, threshold, move_to_images=True))
        return operations

    def _prepare_image(self, image_path: Path, images_dir: Path, threshold: int, *, move_to_images: bool) -> HybridImageOperation:
        source_was_sparse = self._image_type_getter(str(image_path)) == 'sparse'
        if source_was_sparse:
            self._sparse_converter(str(image_path))
        compressed = image_path.stat().st_size > threshold
        if compressed:
            output_path = images_dir / f'{image_path.name}.zst'
            return_code = self._process_call(
                ['zstd', '-5', '--rm', str(image_path), '-o', str(output_path)],
            )
            if return_code not in (0, None) or not output_path.exists():
                raise HybridPackError(f'Unable to compress image: {image_path}')
        else:
            output_path = images_dir / image_path.name
            if move_to_images and image_path.resolve() != output_path.resolve():
                shutil.move(str(image_path), str(output_path))
        return HybridImageOperation(
            image_name=image_path.name,
            compressed=compressed,
            source_was_sparse=source_was_sparse,
            output_path=output_path,
        )

    @staticmethod
    def _write_update_script(script_path: Path, right_device: str, operations: list[HybridImageOperation]) -> None:
        if not script_path.is_file():
            raise HybridTemplateError(f'Hybrid template update-binary is missing: {script_path}')
        lines = script_path.read_text(encoding='utf-8').splitlines(keepends=True)
        marker_index = next((index for index, line in enumerate(lines) if '#Other images' in line), None)
        if marker_index is None:
            raise HybridTemplateError('Hybrid template update-binary has no #Other images marker')
        device_line = f'right_device="{right_device}"\n'
        insertion_index = min(45, len(lines))
        lines.insert(insertion_index, device_line)
        if marker_index >= insertion_index:
            marker_index += 1
        commands = []
        for operation in operations:
            partition = Path(operation.image_name).stem
            if operation.compressed:
                commands.append(
                    f'package_extract_zstd "images/{operation.image_name}.zst" "/dev/block/by-name/{partition}"\n'
                )
            else:
                commands.append(
                    f'package_extract_file "images/{operation.image_name}" "/dev/block/by-name/{partition}"\n'
                )
        lines[marker_index:marker_index] = commands
        with script_path.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(''.join(lines))


__all__ = [
    'HybridPackError',
    'HybridRomPackService',
    'HybridTemplateError',
    'PayloadProjectNotSupportedError',
]
