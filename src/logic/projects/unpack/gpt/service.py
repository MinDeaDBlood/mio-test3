from __future__ import annotations

from pathlib import Path
import os
import re
import tempfile

from src.core.pygpt import GPTReader

from .models import ExtractedGptPartition, GptExtractionResult

_INVALID_FILENAME = re.compile(r'[^A-Za-z0-9._-]+')


def _safe_partition_name(name: str, partition_id, used: set[str]) -> str:
    cleaned = _INVALID_FILENAME.sub('_', name.strip()).strip('._')
    base = cleaned or str(partition_id)
    candidate = base
    index = 2
    while candidate.casefold() in used:
        candidate = f'{base}_{index}'
        index += 1
    used.add(candidate.casefold())
    return candidate


def extract_gpt_partitions(
    image_path: str | Path,
    output_directory: str | Path,
    *,
    sector_size: int = 512,
) -> GptExtractionResult:
    source = Path(image_path)
    output_dir = Path(output_directory)
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f'GPT image was not found or is empty: {source}')
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[ExtractedGptPartition] = []
    created_paths: list[Path] = []
    used_names: set[str] = set()
    try:
        with GPTReader(source, sector_size=sector_size) as reader:
            for entry in reader.partition_table.valid_entries():
                safe_name = _safe_partition_name(entry.name, entry.partition_id, used_names)
                output_path = output_dir / f'{safe_name}.img'
                temporary_path: Path | None = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode='wb',
                        prefix=f'.{output_path.name}.',
                        suffix='.part',
                        dir=output_dir,
                        delete=False,
                    ) as stream:
                        temporary_path = Path(stream.name)
                        for block in reader.block_reader.blocks_in_range(entry.first_block, entry.length):
                            stream.write(block)
                        stream.flush()
                        os.fsync(stream.fileno())
                    expected_size = entry.length * sector_size
                    if temporary_path.stat().st_size != expected_size:
                        raise RuntimeError(
                            f'GPT partition {safe_name} has an unexpected size: '
                            f'{temporary_path.stat().st_size}, expected {expected_size}'
                        )
                    temporary_path.replace(output_path)
                # Every failure must remove the partial partition before it escapes.
                except Exception:
                    if temporary_path is not None:
                        temporary_path.unlink(missing_ok=True)
                    raise
                created_paths.append(output_path)
                extracted.append(
                    ExtractedGptPartition(
                        name=safe_name,
                        partition_id=entry.partition_id,
                        first_sector=entry.first_block,
                        sector_count=entry.length,
                        output_path=output_path,
                    )
                )
    # The extraction is transactional. Any exception must remove every partition
    # already committed by this invocation, then preserve the original exception.
    except Exception:
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise
    if not extracted:
        raise ValueError(f'GPT image does not contain any usable partitions: {source}')
    return GptExtractionResult(source_path=source, partitions=tuple(extracted))


__all__ = ['extract_gpt_partitions']
