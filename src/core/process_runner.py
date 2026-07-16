from __future__ import annotations

import logging
import os
import subprocess
from subprocess import Popen
import time
from typing import BinaryIO

from src.core.diagnostics import emit
from src.core.paths import tool_bin
from src.core.process_registry import process_registry

logger = logging.getLogger(__name__)

if os.name == 'nt':
    from ctypes import windll

    kernel32 = windll.kernel32

    def terminate_process(pid):
        h_process = kernel32.OpenProcess(0x0001, False, pid)
        if h_process:
            kernel32.TerminateProcess(h_process, 0)
            kernel32.CloseHandle(h_process)
        else:
            emit(f'Failed to open process with PID {pid}')
else:

    def terminate_process(pid):
        import signal

        os.kill(pid, signal.SIGKILL)


def _decode_process_line(line: bytes) -> str:
    try:
        return line.decode('utf-8').strip()
    except UnicodeDecodeError:
        return line.decode('gbk', errors='replace').strip()


def _stream_process_output(stream: BinaryIO | None, *, to_stdout: bool) -> None:
    if stream is None:
        return
    for line in iter(stream.readline, b''):
        output = _decode_process_line(line)
        if not output:
            continue
        if to_stdout:
            emit(output)
        else:
            logger.info('process.output: %s', output)


def _resolve_command(exe, *, extra_path: bool):
    if isinstance(exe, list):
        command = list(exe)
        if extra_path and command:
            command[0] = f'{tool_bin}{command[0]}'
        return [item for item in command if item]
    command = f'{tool_bin}{exe}' if extra_path else exe
    if os.name == 'posix':
        return command.split()
    return command


def call(exe, extra_path=True, out: bool = True):
    command = _resolve_command(exe, extra_path=extra_path)
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name != 'posix' else 0
    started = time.perf_counter()
    logger.info(
        'process.start: command=%r extra_path=%s tool_bin=%s',
        command,
        extra_path,
        tool_bin,
    )
    process: Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )
        process_registry.add(process.pid)
        logger.debug('process.spawned: pid=%s command=%r', process.pid, command)
        try:
            _stream_process_output(process.stdout, to_stdout=out)
            return_code = process.wait()
        finally:
            process_registry.discard(process.pid)
        logger.info(
            'process.completed: pid=%s return_code=%s duration=%.3fs command=%r',
            process.pid,
            return_code,
            time.perf_counter() - started,
            command,
        )
        return return_code
    except FileNotFoundError:
        logger.exception(
            'process.executable_not_found: command=%r extra_path=%s tool_bin=%s',
            command,
            extra_path,
            tool_bin,
        )
        return 2
    except OSError:
        logger.exception(
            'process.os_error: command=%r extra_path=%s tool_bin=%s',
            command,
            extra_path,
            tool_bin,
        )
        return 2
    finally:
        if process is not None and process.poll() is None:
            logger.warning(
                'process.still_running_during_cleanup: pid=%s command=%r',
                process.pid,
                command,
            )


__all__ = ['call', 'terminate_process']
