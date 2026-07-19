from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


from pathlib import Path
import struct
import zlib
from uuid import UUID

from src.core.file_types import gettype
from src.core.pygpt import GPTReader
from src.logic.projects.unpack.gpt import extract_gpt_partitions


def _build_gpt_image(path: Path) -> bytes:
    sector_size = 512
    total_sectors = 128
    entry_count = 128
    entry_size = 128
    first_sector = 40
    last_sector = 42
    partition_data = bytes((index % 251 for index in range((last_sector - first_sector + 1) * sector_size)))
    image = bytearray(total_sectors * sector_size)

    entries = bytearray(entry_count * entry_size)
    name = 'system'.encode('utf-16-le').ljust(72, b'\x00')
    entry = struct.pack(
        '<16s16sQQQ72s',
        UUID('0fc63daf-8483-4772-8e79-3d69d8477de4').bytes_le,
        UUID('11111111-2222-3333-4444-555555555555').bytes_le,
        first_sector,
        last_sector,
        0,
        name,
    )
    entries[:len(entry)] = entry
    entry_crc = zlib.crc32(entries) & 0xFFFFFFFF
    image[2 * sector_size:2 * sector_size + len(entries)] = entries

    header_values = [
        b'EFI PART',
        0x00010000,
        92,
        0,
        0,
        1,
        total_sectors - 1,
        34,
        total_sectors - 34,
        UUID('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee').bytes_le,
        2,
        entry_count,
        entry_size,
        entry_crc,
    ]
    header = bytearray(struct.pack('<8sIIIIQQQQ16sQIII', *header_values))
    header_crc = zlib.crc32(header) & 0xFFFFFFFF
    struct.pack_into('<I', header, 16, header_crc)
    image[sector_size:sector_size + len(header)] = header
    image[first_sector * sector_size:(last_sector + 1) * sector_size] = partition_data
    path.write_bytes(image)
    return partition_data


def test_gpt_reader_validates_and_extracts_partition(tmp_path: Path) -> None:
    source = tmp_path / 'disk.img'
    expected = _build_gpt_image(source)

    assert gettype(str(source)) == 'gpt'
    with GPTReader(source) as reader:
        entries = tuple(reader.partition_table.valid_entries())
        assert len(entries) == 1
        assert entries[0].name == 'system'
        assert entries[0].first_block == 40
        assert entries[0].length == 3

    result = extract_gpt_partitions(source, tmp_path / 'out')
    assert len(result.partitions) == 1
    assert result.partitions[0].output_path.name == 'system.img'
    assert result.partitions[0].output_path.read_bytes() == expected


def test_gpt_reader_rejects_corrupt_entry_crc(tmp_path: Path) -> None:
    source = tmp_path / 'disk.img'
    _build_gpt_image(source)
    data = bytearray(source.read_bytes())
    data[2 * 512] ^= 0xFF
    source.write_bytes(data)

    try:
        GPTReader(source)
    except ValueError as exc:
        assert 'CRC mismatch' in str(exc)
    else:
        raise AssertionError('Corrupt GPT entry table was accepted')

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
