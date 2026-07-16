from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.core.process_runner import call


@dataclass(frozen=True)
class ImgkitUnpackResult:
    input_path: Path
    output_directory: Path
    fs_config_path: Path | None
    file_contexts_path: Path | None


ProcessCall = Callable[..., int]


def unpack_image(
    input_path: str | Path,
    output_directory: str | Path,
    *,
    fs_config_path: str | Path | None = None,
    file_contexts_path: str | Path | None = None,
    clean: bool = False,
    log_level: int = 1,
    process_call: ProcessCall = call,
) -> ImgkitUnpackResult:
    source = Path(input_path)
    destination = Path(output_directory)
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f'Image was not found or is empty: {source}')
    if not 0 <= int(log_level) <= 3:
        raise ValueError('imgkit log level must be between 0 and 3')
    destination.mkdir(parents=True, exist_ok=True)
    fs_path = Path(fs_config_path) if fs_config_path is not None else None
    contexts_path = Path(file_contexts_path) if file_contexts_path is not None else None
    if fs_path is not None:
        fs_path.parent.mkdir(parents=True, exist_ok=True)
    if contexts_path is not None:
        contexts_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        'imgkit',
        'unpack',
        '-i',
        str(source),
        '-o',
        str(destination),
        '-l',
        str(int(log_level)),
    ]
    if fs_path is not None:
        command.extend(['--fs-config-path', str(fs_path)])
    if contexts_path is not None:
        command.extend(['--file-contexts-path', str(contexts_path)])
    if clean:
        command.append('--clean')
    return_code = process_call(exe=command, out=False)
    if return_code != 0:
        raise RuntimeError(f'imgkit unpack failed with exit code {return_code}: {source}')
    return ImgkitUnpackResult(
        input_path=source,
        output_directory=destination,
        fs_config_path=fs_path,
        file_contexts_path=contexts_path,
    )


__all__ = ['ImgkitUnpackResult', 'unpack_image']
