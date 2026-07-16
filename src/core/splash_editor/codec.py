from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import math
import struct

from PIL import Image

SPLASH_MAGIC = b'SPLASH!!'
SECTOR_SIZE = 512
CONTAINER_PREFIX_SIZE = 1024
DEFAULT_PAYLOAD_LIMITS: tuple[int, ...] = (100864, 613888, 101888, 204288, 204288, 0, 0, 0)


class SplashFormatError(ValueError):
    """Raised when a Qualcomm splash image is malformed or unsupported."""


@dataclass(frozen=True)
class SplashEntry:
    width: int
    height: int
    compressed: bool
    payload_size: int
    image: Image.Image


def _rgb_image(image: Image.Image) -> Image.Image:
    if image.mode == 'RGB':
        return image.copy()
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (0, 0, 0))
        background.paste(image, mask=image.getchannel('A'))
        return background
    return image.convert('RGB')


def _encode_literal(pixels: list[tuple[int, int, int]]) -> bytes:
    if not 1 <= len(pixels) <= 128:
        raise ValueError('Literal RLE run must contain between 1 and 128 pixels')
    output = bytearray((len(pixels) - 1,))
    for red, green, blue in pixels:
        output.extend((blue, green, red))
    return bytes(output)


def _encode_repeat(pixel: tuple[int, int, int], count: int) -> bytes:
    if not 1 <= count <= 128:
        raise ValueError('Repeated RLE run must contain between 1 and 128 pixels')
    red, green, blue = pixel
    return bytes((127 + count, blue, green, red))


def encode_rle24(image: Image.Image) -> bytes:
    """Encode an image using the Qualcomm splash RLE24 stream format."""
    rgb = _rgb_image(image)
    output = bytearray()
    for y in range(rgb.height):
        row = [rgb.getpixel((x, y)) for x in range(rgb.width)]
        index = 0
        literal: list[tuple[int, int, int]] = []
        while index < len(row):
            run_length = 1
            while (
                index + run_length < len(row)
                and row[index + run_length] == row[index]
                and run_length < 128
            ):
                run_length += 1
            if run_length >= 2:
                if literal:
                    output.extend(_encode_literal(literal))
                    literal.clear()
                output.extend(_encode_repeat(row[index], run_length))
                index += run_length
                continue
            literal.append(row[index])
            index += 1
            if len(literal) == 128:
                output.extend(_encode_literal(literal))
                literal.clear()
        if literal:
            output.extend(_encode_literal(literal))
    return bytes(output)


def decode_rle24(payload: bytes, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        raise SplashFormatError(f'Invalid splash resolution: {width}x{height}')
    pixel_total = width * height
    decoded: list[tuple[int, int, int]] = []
    stream = BytesIO(payload)
    while len(decoded) < pixel_total:
        control_raw = stream.read(1)
        if not control_raw:
            raise SplashFormatError('Splash RLE payload ended before all pixels were decoded')
        count_code = control_raw[0] + 1
        if count_code > 128:
            pixel_raw = stream.read(3)
            if len(pixel_raw) != 3:
                raise SplashFormatError('Splash RLE repeated pixel is truncated')
            blue, green, red = pixel_raw
            decoded.extend([(red, green, blue)] * (count_code - 128))
        else:
            raw = stream.read(count_code * 3)
            if len(raw) != count_code * 3:
                raise SplashFormatError('Splash RLE literal run is truncated')
            decoded.extend((raw[i + 2], raw[i + 1], raw[i]) for i in range(0, len(raw), 3))
        if len(decoded) > pixel_total:
            raise SplashFormatError('Splash RLE payload contains more pixels than the header declares')
    image = Image.new('RGB', (width, height))
    image.putdata(decoded)
    return image


def _build_header(*, width: int, height: int, compressed: bool, payload_size: int) -> bytes:
    if payload_size <= 0 or payload_size % SECTOR_SIZE:
        raise ValueError('Splash payload must be a positive multiple of 512 bytes')
    header = bytearray(SECTOR_SIZE)
    header[:8] = SPLASH_MAGIC
    struct.pack_into('<IIII', header, 8, width, height, int(compressed), payload_size // SECTOR_SIZE)
    return bytes(header)


def encode_entry(image: Image.Image, *, payload_limit: int = 0) -> bytes:
    rgb = _rgb_image(image)
    encoded = encode_rle24(rgb)
    minimum_padded_size = math.ceil(len(encoded) / SECTOR_SIZE) * SECTOR_SIZE
    padded_size = payload_limit or minimum_padded_size
    if padded_size % SECTOR_SIZE:
        raise ValueError('Splash payload limit must be a multiple of 512 bytes')
    if len(encoded) > padded_size:
        raise ValueError(
            f'Encoded splash image requires {len(encoded)} bytes, but only {padded_size} bytes are available'
        )
    payload = encoded + (b'\x00' * (padded_size - len(encoded)))
    return _build_header(
        width=rgb.width,
        height=rgb.height,
        compressed=True,
        payload_size=padded_size,
    ) + payload


def decode_entries(source: str | Path) -> tuple[SplashEntry, ...]:
    source_path = Path(source)
    entries: list[SplashEntry] = []
    with source_path.open('rb') as stream:
        prefix = stream.read(CONTAINER_PREFIX_SIZE)
        if len(prefix) != CONTAINER_PREFIX_SIZE:
            raise SplashFormatError('Splash image is smaller than its 1024 byte prefix')
        while True:
            magic = stream.read(len(SPLASH_MAGIC))
            if not magic:
                break
            if magic == b'\x00' * len(SPLASH_MAGIC):
                while magic and all(value == 0 for value in magic):
                    magic = stream.read(len(SPLASH_MAGIC))
                if not magic:
                    break
            if magic != SPLASH_MAGIC:
                raise SplashFormatError(f'Unexpected data at offset {stream.tell() - len(magic)}')
            fields = stream.read(16)
            if len(fields) != 16:
                raise SplashFormatError('Splash entry header is truncated')
            width, height, compressed, payload_blocks = struct.unpack('<IIII', fields)
            stream.seek(SECTOR_SIZE - 24, 1)
            payload_size = payload_blocks * SECTOR_SIZE
            if payload_size <= 0:
                raise SplashFormatError('Splash entry declares an empty payload')
            payload = stream.read(payload_size)
            if len(payload) != payload_size:
                raise SplashFormatError('Splash entry payload is truncated')
            if compressed != 1:
                raise SplashFormatError(f'Unsupported splash compression type: {compressed}')
            image = decode_rle24(payload, width, height)
            entries.append(
                SplashEntry(
                    width=width,
                    height=height,
                    compressed=True,
                    payload_size=payload_size,
                    image=image,
                )
            )
    if not entries:
        raise SplashFormatError('No Qualcomm splash entries were found')
    return tuple(entries)


__all__ = [
    'CONTAINER_PREFIX_SIZE',
    'DEFAULT_PAYLOAD_LIMITS',
    'SECTOR_SIZE',
    'SPLASH_MAGIC',
    'SplashEntry',
    'SplashFormatError',
    'decode_entries',
    'decode_rle24',
    'encode_entry',
    'encode_rle24',
]
