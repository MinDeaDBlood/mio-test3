from __future__ import annotations
from src.core.diagnostics import emit

import logging
import os
import subprocess
from subprocess import Popen

from src.core.paths import tool_bin
from src.core.process_registry import process_registry

if os.name == 'nt':
    from ctypes import windll

    kernel32 = windll.kernel32

    def terminate_process(pid):
        h_process = kernel32.OpenProcess(0x0001, False, pid)
        if h_process:
            kernel32.TerminateProcess(h_process, 0)
            kernel32.CloseHandle(h_process)
        else:
            emit(f"Failed to open process with PID {pid}")
else:
    def terminate_process(pid):
        import signal
        os.kill(pid, signal.SIGKILL)


def _stream_process_output(inp: subprocess.CalledProcessError | Popen[bytes], *, to_stdout: bool) -> None:
    for line in iter(inp.stdout.readline, b""):
        try:
            out_put = line.decode("utf-8").strip()
        except UnicodeDecodeError:
            out_put = line.decode("gbk").strip()
        if to_stdout:
            emit(out_put)
        else:
            logging.info(out_put)


def call(exe, extra_path=True, out: bool = True):
    logging.info(exe)
    if isinstance(exe, list):
        cmd = list(exe)
        if extra_path:
            cmd[0] = f"{tool_bin}{cmd[0]}"
        cmd = [item for item in cmd if item]
    else:
        cmd = f'{tool_bin}{exe}' if extra_path else exe
        if os.name == 'posix':
            cmd = cmd.split()
    conf = subprocess.CREATE_NO_WINDOW if os.name != 'posix' else 0
    try:
        ret = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, creationflags=conf)
        pid = ret.pid
        process_registry.add(pid)
        try:
            _stream_process_output(ret, to_stdout=out)
        finally:
            process_registry.discard(pid)
    except subprocess.CalledProcessError as e:
        _stream_process_output(e, to_stdout=out)
        return 2
    except FileNotFoundError:
        logging.exception('process_runner.executable_not_found: cmd=%r; extra_path=%s; tool_bin=%s', cmd, extra_path, tool_bin)
        return 2
    ret.wait()
    return ret.returncode


__all__ = ['call', 'terminate_process']
