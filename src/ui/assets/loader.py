from __future__ import annotations

from pathlib import Path

from PIL.Image import open as open_img
from PIL.ImageTk import PhotoImage


def load_photo_image(path: str | Path, *, size: tuple[int, int] | None = None):
    source = Path(path)
    with source.open('rb') as stream:
        image = open_img(stream)
        if size is not None:
            image = image.resize(size)
        return PhotoImage(image)


__all__ = ['load_photo_image']
