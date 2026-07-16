from __future__ import annotations

import os
from pathlib import Path

from src.core.lpunpack import SparseImage
from src.core.process_runner import call


def simg2img(path: str) -> bool:
    """Convert a sparse image in place and report whether conversion occurred."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    with image_path.open('rb') as stream:
        sparse_image = SparseImage(stream)
        if not sparse_image.check():
            return False
        unsparse_file = sparse_image.unsparse()
    if not unsparse_file:
        raise RuntimeError(f'Sparse conversion produced no output for {image_path}')
    unsparse_path = Path(unsparse_file)
    if not unsparse_path.is_file():
        raise RuntimeError(f'Sparse conversion output is missing: {unsparse_path}')
    os.replace(unsparse_path, image_path)
    return True


def img2simg(path: str) -> bool:
    """Convert a raw image in place to Android sparse format."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    sparse_path = Path(f'{path}s')
    if sparse_path.exists():
        sparse_path.unlink()
    return_code = call(['img2simg', str(image_path), str(sparse_path)])
    if return_code not in (0, None):
        raise RuntimeError(f'img2simg failed with exit code {return_code}: {image_path}')
    if not sparse_path.is_file():
        raise RuntimeError(f'img2simg produced no output: {sparse_path}')
    os.replace(sparse_path, image_path)
    return True


__all__ = ['simg2img', 'img2simg']
