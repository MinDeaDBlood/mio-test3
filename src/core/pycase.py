#!/usr/bin/env python3
# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Set a directory case-sensitive on Windows directly with ctypes.

Notes
-----
- Requires NTFS + WSL case-sensitivity support.
- Windows only allows changing the flag on an empty directory.
- The helper is best-effort by default: expected environmental failures do not
  raise, because case sensitivity is an optimization for mixed-case Android
  files rather than a hard requirement for every workflow.
"""

from ctypes import (
    WinDLL,
    c_void_p,
    get_last_error,
    WinError,
    c_int,
    Structure,
    sizeof,
    byref,
)
from ctypes.wintypes import (
    HANDLE,
    LPCWSTR,
    DWORD,
    BOOL,
    LPVOID,
    ULONG,
)

try:
    from enum import IntEnum
except ImportError:
    IntEnum = int

import os
import os.path

# ==================================================================
# ======================== WinApi Bindings =========================
# ==================================================================

kernel32 = WinDLL('kernel32', use_last_error=True)


# Known Win32 error codes that should not blow up the application.
ERROR_INVALID_FUNCTION = 1
ERROR_ACCESS_DENIED = 5
ERROR_NOT_SUPPORTED = 50
ERROR_INVALID_PARAMETER = 87
ERROR_DIR_NOT_EMPTY = 145
ERROR_ALREADY_EXISTS = 183

NON_FATAL_CASE_SENSITIVITY_ERRORS = {
    ERROR_INVALID_FUNCTION,
    ERROR_ACCESS_DENIED,
    ERROR_NOT_SUPPORTED,
    ERROR_INVALID_PARAMETER,
    ERROR_DIR_NOT_EMPTY,
    ERROR_ALREADY_EXISTS,
}


def _check_handle(h, *_):
    if h == INVALID_HANDLE_VALUE:
        raise WinError(get_last_error())
    return h


def _expect_nonzero(res, *_):
    if not res:
        raise WinError(get_last_error())


FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_POSIX_SEMANTICS = 0x01000000

OPEN_EXISTING = 3

FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
FILE_SHARE_VALID_FLAGS = FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

_CreateFileW = kernel32.CreateFileW
_CreateFileW.argtypes = [
    LPCWSTR, DWORD, DWORD, c_void_p, DWORD, DWORD, HANDLE
]
_CreateFileW.restype = HANDLE
_CreateFileW.errcheck = _check_handle

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000

INVALID_HANDLE_VALUE = HANDLE(-1).value

_CloseHandle = kernel32.CloseHandle
_CloseHandle.argtypes = [HANDLE]
_CloseHandle.restype = BOOL
_CloseHandle.errcheck = _expect_nonzero

_GetFileInformationByHandleEx = kernel32.GetFileInformationByHandleEx
_GetFileInformationByHandleEx.argtypes = [HANDLE, c_int, LPVOID, DWORD]
_GetFileInformationByHandleEx.restype = BOOL
_GetFileInformationByHandleEx.errcheck = _expect_nonzero


class FILE_CASE_SENSITIVE_INFO(Structure):
    _fields_ = [
        ('Flags', ULONG)
    ]


FILE_INFO_BY_HANDLE = FILE_CASE_SENSITIVE_INFO


class FILE_INFO_BY_HANDLE_CLASS(IntEnum):
    FileCaseSensitiveInfo = 23


FILE_CS_FLAG_CASE_SENSITIVE_DIR = 0x00000001

_SetFileInformationByHandle = kernel32.SetFileInformationByHandle
_SetFileInformationByHandle.argtypes = [HANDLE, c_int, LPVOID, DWORD]
_SetFileInformationByHandle.restype = BOOL
_SetFileInformationByHandle.errcheck = _expect_nonzero


# ==================================================================
# ======================= Wrappers functions =======================
# ==================================================================


def CreateFileW(path: str, access: int, share: int,
                oflag: int, flags: int) -> HANDLE:
    return _CreateFileW(
        os.fsdecode(path),
        access, share,
        None,
        oflag, flags,
        None,
    )



def CloseHandle(h: HANDLE):
    _CloseHandle(h)



def GetFileInformationByHandleEx(
        h: HANDLE,
        kind: FILE_INFO_BY_HANDLE_CLASS
) -> FILE_INFO_BY_HANDLE:
    if kind == FILE_INFO_BY_HANDLE_CLASS.FileCaseSensitiveInfo:
        dtype = FILE_CASE_SENSITIVE_INFO
    else:
        raise ValueError('Invalid file info class')

    data = dtype()
    _GetFileInformationByHandleEx(h, kind, byref(data), sizeof(dtype))
    return data



def SetFileInformationByHandle(
        h: HANDLE,
        kind: FILE_INFO_BY_HANDLE_CLASS,
        data: FILE_INFO_BY_HANDLE
):
    if kind == FILE_INFO_BY_HANDLE_CLASS.FileCaseSensitiveInfo:
        dtype = FILE_CASE_SENSITIVE_INFO
    else:
        raise ValueError('Invalid file info class')

    _SetFileInformationByHandle(h, kind, byref(data), sizeof(dtype))


# ==================================================================
# ======================== Helper functions ========================
# ==================================================================


def open_dir_handle(path: str, access: int) -> HANDLE:
    return CreateFileW(
        path, access,
        FILE_SHARE_VALID_FLAGS, OPEN_EXISTING,
        FILE_FLAG_POSIX_SEMANTICS | FILE_FLAG_BACKUP_SEMANTICS
    )



def _directory_is_empty(path: str) -> bool:
    with os.scandir(path) as entries:
        return next(entries, None) is None



def _is_expected_case_sensitivity_error(exc: OSError) -> bool:
    if not isinstance(exc, OSError) or not hasattr(exc, 'winerror'):
        return False
    return exc.winerror in NON_FATAL_CASE_SENSITIVITY_ERRORS


# ==================================================================
# ======================= Exported functions ========================
# ==================================================================


def ensure_dir_case_sensitive(path: str, strict: bool = False) -> bool:
    """Enable per-directory case sensitivity on Windows.

    Returns True when the directory is already case-sensitive or was switched
    successfully. Returns False for known environmental limitations such as a
    non-empty directory, unsupported filesystem, or insufficient privileges.

    Args:
        path: Directory path.
        strict: Re-raise expected environmental errors instead of returning
            False. Unexpected errors always propagate.
    """
    if not os.path.isdir(path):
        raise NotADirectoryError(
            f'Cannot set case sensitive for non-directory: {path}'
        )

    h = open_dir_handle(path, GENERIC_READ)
    try:
        info: FILE_CASE_SENSITIVE_INFO = GetFileInformationByHandleEx(
            h, FILE_INFO_BY_HANDLE_CLASS.FileCaseSensitiveInfo
        )

        if info.Flags & FILE_CS_FLAG_CASE_SENSITIVE_DIR:
            return True

        # Windows requires the directory to be empty before toggling the flag.
        if not _directory_is_empty(path):
            if strict:
                raise WinError(ERROR_DIR_NOT_EMPTY)
            return False

        h2 = open_dir_handle(path, GENERIC_WRITE)
        try:
            info.Flags |= FILE_CS_FLAG_CASE_SENSITIVE_DIR
            try:
                SetFileInformationByHandle(
                    h2,
                    FILE_INFO_BY_HANDLE_CLASS.FileCaseSensitiveInfo,
                    info,
                )
            except OSError as exc:
                if strict or not _is_expected_case_sensitivity_error(exc):
                    raise
                return False
            return True
        finally:
            CloseHandle(h2)
    finally:
        CloseHandle(h)
