from __future__ import annotations

import shutil
import tempfile
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from src.core.url_paths import download_filename
from src.logic.network_downloads import download_api


@dataclass(frozen=True)
class FirmwareDownloadProgress:
    percentage: int | float | str
    speed: int | float
    bytes_downloaded: int
    file_size: int


@dataclass(frozen=True)
class FirmwareDownloadResult:
    file_path: Path | None
    elapsed: float
    imported: bool


class DownloadFirmwareUseCase:
    def __init__(
        self,
        *,
        downloader: Callable[..., Iterable[tuple]] = download_api,
        importer: Callable[[str], object] | None = None,
    ):
        self.downloader = downloader
        self.importer = importer

    def execute(
        self,
        *,
        url: str,
        output_dir: str | Path,
        auto_import: bool | Callable[[], bool],
        on_progress: Callable[[FirmwareDownloadProgress], None],
    ) -> FirmwareDownloadResult:
        filename = download_filename(url)
        target_dir = Path(output_dir).resolve()
        if not target_dir.is_dir():
            raise FileNotFoundError(target_dir)
        target_file = target_dir / filename
        if target_file.exists():
            raise FileExistsError(f'Download target already exists: {target_file}')

        staging_dir = Path(tempfile.mkdtemp(prefix='.mio_download_', dir=target_dir))
        staged_file = staging_dir / filename
        started = time.monotonic()
        imported = False
        try:
            for percentage, speed, downloaded, file_size, _elapsed in self.downloader(url, str(staging_dir)):
                if percentage == 'Error':
                    raise RuntimeError('Firmware download failed')
                on_progress(
                    FirmwareDownloadProgress(
                        percentage=percentage,
                        speed=speed,
                        bytes_downloaded=downloaded,
                        file_size=file_size,
                    )
                )
            if not staged_file.is_file():
                raise RuntimeError(f'Download finished without an output file: {staged_file}')

            import_requested = auto_import() if callable(auto_import) else auto_import
            if import_requested:
                if self.importer is None:
                    raise RuntimeError('Automatic firmware import requires an explicit importer.')
                self.importer(str(staged_file))
                imported = True
                result_path = None
            else:
                staged_file.replace(target_file)
                result_path = target_file
            return FirmwareDownloadResult(
                file_path=result_path,
                elapsed=time.monotonic() - started,
                imported=imported,
            )
        finally:
            if staging_dir.exists():
                shutil.rmtree(staging_dir)


__all__ = ['DownloadFirmwareUseCase', 'FirmwareDownloadProgress', 'FirmwareDownloadResult']
