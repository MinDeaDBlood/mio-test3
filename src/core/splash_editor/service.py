from __future__ import annotations

from pathlib import Path
import os
import tempfile

from .codec import CONTAINER_PREFIX_SIZE, DEFAULT_PAYLOAD_LIMITS, decode_entries, encode_entry


def _splash_image_paths(input_dir: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for index in range(1, len(DEFAULT_PAYLOAD_LIMITS) + 1):
        path = input_dir / f'splash{index}.png'
        if not path.is_file():
            break
        paths.append(path)
    if not paths:
        raise FileNotFoundError(f'No splash1.png was found in {input_dir}')
    return tuple(paths)


def splash_repack(input_dir: str | Path, output_file: str | Path, nolimit: bool = False) -> Path:
    """Pack splash1.png and following images into a Qualcomm splash image."""
    source_dir = Path(input_dir)
    output_path = Path(output_file)
    image_paths = _splash_image_paths(source_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='wb',
            prefix=f'.{output_path.name}.',
            suffix='.part',
            dir=output_path.parent,
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(b'\x00' * CONTAINER_PREFIX_SIZE)
            for index, image_path in enumerate(image_paths):
                from PIL import Image

                with Image.open(image_path) as image:
                    limit = 0 if nolimit else DEFAULT_PAYLOAD_LIMITS[index]
                    stream.write(encode_entry(image, payload_limit=limit))
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(output_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    if not output_path.is_file() or output_path.stat().st_size <= CONTAINER_PREFIX_SIZE:
        raise RuntimeError(f'Splash image was not created correctly: {output_path}')
    return output_path


def process_splashimg(input_file: str | Path, output_file: str | Path) -> tuple[Path, ...]:
    """Extract every splash entry as splash1.png, splash2.png and so on."""
    source_path = Path(input_file)
    output_template = Path(output_file)
    output_template.parent.mkdir(parents=True, exist_ok=True)
    entries = decode_entries(source_path)
    suffix = output_template.suffix or '.png'
    stem = output_template.stem if output_template.suffix else output_template.name
    output_paths: list[Path] = []
    for index, entry in enumerate(entries, start=1):
        output_path = output_template.parent / f'{stem}{index}{suffix}'
        entry.image.save(output_path, format='PNG')
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError(f'Splash image was not extracted correctly: {output_path}')
        output_paths.append(output_path)
    return tuple(output_paths)


__all__ = ['process_splashimg', 'splash_repack']
