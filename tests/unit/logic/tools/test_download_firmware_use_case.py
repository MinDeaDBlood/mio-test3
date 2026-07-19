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

import pytest

from src.logic.tools.download_firmware.use_case import DownloadFirmwareUseCase


def _downloader(payload: bytes):
    def download(url, output_dir):
        filename = url.split('?', 1)[0].rsplit('/', 1)[-1]
        Path(output_dir, filename).write_bytes(payload)
        yield 100, 1, len(payload), len(payload), 0
    return download


def test_download_uses_staging_and_preserves_result(tmp_path: Path):
    result = DownloadFirmwareUseCase(downloader=_downloader(b'firmware')).execute(
        url='https://example.test/rom.zip?token=secret',
        output_dir=tmp_path,
        auto_import=False,
        on_progress=lambda _progress: None,
    )

    assert result.file_path == tmp_path / 'rom.zip'
    assert result.file_path.read_bytes() == b'firmware'
    assert not list(tmp_path.glob('.mio_download_*'))


def test_download_does_not_overwrite_existing_file(tmp_path: Path):
    target = tmp_path / 'rom.zip'
    target.write_bytes(b'original')

    with pytest.raises(FileExistsError):
        DownloadFirmwareUseCase(downloader=_downloader(b'new')).execute(
            url='https://example.test/rom.zip',
            output_dir=tmp_path,
            auto_import=False,
            on_progress=lambda _progress: None,
        )

    assert target.read_bytes() == b'original'


def test_auto_import_receives_staged_file_and_leaves_no_archive(tmp_path: Path):
    imported: list[bytes] = []

    def importer(path: str):
        imported.append(Path(path).read_bytes())

    result = DownloadFirmwareUseCase(downloader=_downloader(b'firmware'), importer=importer).execute(
        url='https://example.test/rom.zip',
        output_dir=tmp_path,
        auto_import=True,
        on_progress=lambda _progress: None,
    )

    assert imported == [b'firmware']
    assert result.imported is True
    assert result.file_path is None
    assert not (tmp_path / 'rom.zip').exists()
    assert not list(tmp_path.glob('.mio_download_*'))

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
