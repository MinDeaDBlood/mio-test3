from __future__ import annotations

import logging
import os
import time

import requests

from src.core.url_paths import download_filename


def download_api(url: str, path: str, int_=True, size_: int = 0, chunk_size: int = 2048576):
    """Yield download progress tuples.

    Returns: percentage, speed, bytes_downloaded, file_size, elapsed
    """
    start_time = time.time()
    session = requests.Session()

    try:
        response_head = session.head(url, timeout=10)
        response_head.raise_for_status()
        file_size = int(response_head.headers.get("Content-Length", 0))
    except requests.exceptions.RequestException as exc:
        logging.error('Error making HEAD request to %s: %s', url, exc)
        file_size = 0

    try:
        response_get = session.get(url, stream=True, timeout=10)
        response_get.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logging.error('Error making GET request to %s: %s', url, exc)
        yield 'Error', 0, 0, 0, 0
        return

    last_time = time.time()
    if file_size == 0 and size_ > 0:
        file_size = size_
    if not path:
        raise ValueError('Download output path is required')
    os.makedirs(path, exist_ok=True)
    file_save_path = os.path.join(path, download_filename(url))
    logging.info('Starting download: %s to %s, expected size: %s', url, file_save_path, file_size)

    bytes_downloaded = 0
    try:
        with open(file_save_path, 'wb') as handle:
            for data in response_get.iter_content(chunk_size=chunk_size):
                if not data:
                    break
                handle.write(data)
                bytes_downloaded += len(data)
                current_time = time.time()
                elapsed_total = current_time - start_time
                time_since_last_chunk = current_time - last_time
                speed = 0
                if time_since_last_chunk > 0.001:
                    speed = (len(data) / 1024) / time_since_last_chunk
                elif elapsed_total > 0.001:
                    speed = (bytes_downloaded / 1024) / elapsed_total
                last_time = current_time
                percentage = 'Unknown'
                if file_size > 0:
                    percentage_float = (bytes_downloaded / file_size) * 100
                    percentage = int(percentage_float) if int_ else percentage_float
                yield percentage, speed, bytes_downloaded, file_size, elapsed_total
    except (OSError, requests.exceptions.RequestException) as exc:
        logging.error('Download or file write failed for %s: %s', file_save_path, exc)
        yield 'Error', 0, bytes_downloaded, file_size, time.time() - start_time
    else:
        logging.info('Finished download: %s to %s, total bytes: %s', url, file_save_path, bytes_downloaded)
