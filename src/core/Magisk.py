# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0.
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path


class MagiskPatchError(RuntimeError):
    """Raised when a boot image cannot be patched safely."""


OutputSink = Callable[[str], object]


def _discard_output(_message: str) -> None:
    return None


class Magisk_patch:
    """Low level Magisk boot patcher.

    The class contains no UI interaction and never terminates the process. Errors
    are reported with exceptions and progress is sent through ``output_sink``.
    The historical class name is kept because it is part of the public API.
    """

    def __init__(
        self,
        boot_img,
        Magisk_dir,
        magiskboot,
        local,
        IS64BIT=True,
        KEEPVERITY=False,
        KEEPFORCEENCRYPT=False,
        RECOVERYMODE=False,
        MAGISAPK=None,
        PATCH_ARCH=None,
        output_sink: OutputSink | None = None,
    ):
        self.output = None
        self.SKIPBACKUP = ''
        self.SKIPSTUB = ''
        self.SKIP64 = ''
        self.SKIP32 = ''
        self.SHA1 = None
        self.init = 'init'
        self.STATUS = None
        self.MAGISKAPK = MAGISAPK
        self.CHROMEOS = None
        self.custom = False
        self.IS64BIT = IS64BIT
        self.PATCH_ARCH = PATCH_ARCH
        self.KEEPVERITY = KEEPVERITY
        self.KEEPFORCEENCRYPT = KEEPFORCEENCRYPT
        self.RECOVERYMODE = RECOVERYMODE
        self.Magisk_dir = Magisk_dir
        self.magiskboot = magiskboot
        self.boot_img = boot_img
        self.local = local
        self._output_sink = output_sink or _discard_output

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _emit(self, message: object) -> None:
        self._output_sink(str(message))

    def auto_patch(self):
        self._emit('Magisk Boot Patcher')
        if not self.local:
            raise MagiskPatchError('Magisk working directory is not configured')
        if self.boot_img == os.path.join(self.local, 'new-boot.img'):
            raise MagiskPatchError(f'Input image must be renamed: {self.boot_img}')
        executable = self.magiskboot + ('.exe' if os.name == 'nt' and not str(self.magiskboot).lower().endswith('.exe') else '')
        if not self.boot_img or not os.path.exists(self.boot_img):
            raise FileNotFoundError(f'Boot image does not exist: {self.boot_img}')
        if not self.magiskboot or not os.path.exists(executable):
            raise FileNotFoundError(f'magiskboot executable does not exist: {executable}')

        os.makedirs(self.local, exist_ok=True)
        real_cwd = os.getcwd()
        try:
            os.chdir(self.local)
            if self.MAGISKAPK:
                self.extract_magisk()
            self.unpack()
            self.check()
            self.patch()
            self.patch_kernel()
            self.repack()
            self.cleanup()
        finally:
            os.chdir(real_cwd)
        return self.output

    def exec(self, *args, out=0):
        full = [self.magiskboot, *args]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            process = subprocess.Popen(
                full,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise MagiskPatchError(f'Cannot execute magiskboot: {exc}') from exc

        assert process.stdout is not None
        for line in iter(process.stdout.readline, b''):
            if out == 0:
                text = line.decode('utf-8', 'ignore').strip()
                if text:
                    self._emit(text)
        return process.wait()

    def unpack(self):
        ret = self.exec('unpack', self.boot_img)
        if ret == 1:
            raise MagiskPatchError('Unsupported or unknown boot image format')
        if ret == 2:
            self.CHROMEOS = True
            raise MagiskPatchError('ChromeOS boot images are not supported')
        if ret != 0:
            raise MagiskPatchError(f'Unable to unpack boot image, magiskboot exit code: {ret}')
        if os.path.exists(os.path.join(self.local, 'recovery_dtbo')):
            self.RECOVERYMODE = True

    def check(self):
        self._emit('Checking ramdisk status')
        ramdisk = os.path.join(self.local, 'ramdisk.cpio')
        self.STATUS = self.exec('cpio', 'ramdisk.cpio', 'test') if os.path.exists(ramdisk) else 0
        if (self.STATUS & 3) == 0:
            self._emit('Stock boot image detected')
            self.SHA1 = self.sha1(self.boot_img)
            shutil.copyfile(self.boot_img, os.path.join(self.local, 'stock_boot.img'))
            if os.path.exists(ramdisk):
                shutil.copyfile(ramdisk, os.path.join(self.local, 'ramdisk.cpio.orig'))
            else:
                self.SKIPBACKUP = '#'
        elif (self.STATUS & 3) == 1:
            self._emit('Magisk patched boot image detected')
            if not self.SHA1:
                self.SHA1 = self.sha1(ramdisk)
            self.exec('cpio', 'ramdisk.cpio', 'restore')
            shutil.copyfile(ramdisk, os.path.join(self.local, 'ramdisk.cpio.orig'))
            self.remove('stock_boot.img')
        elif (self.STATUS & 3) == 2:
            raise MagiskPatchError('Boot image was patched by an unsupported program. Restore the stock image first.')
        if self.STATUS & 4:
            self.init = 'init.real'

    def patch(self):
        self._emit('Patching ramdisk')
        with open(os.path.join(self.local, 'config'), 'w', encoding='utf-8', newline='\n') as config:
            config.write(f'KEEPVERITY={str(self.KEEPVERITY).lower()}\n')
            config.write(f'KEEPFORCEENCRYPT={str(self.KEEPFORCEENCRYPT).lower()}\n')
            config.write(f'RECOVERYMODE={str(self.RECOVERYMODE).lower()}\n')
            if self.SHA1:
                config.write(f'SHA1={self.SHA1}')
        self.SKIP64 = '' if self.IS64BIT else '#'
        if self.Magisk_dir and os.path.exists(os.path.join(self.Magisk_dir, 'magisk32')):
            self.exec('compress=xz', os.path.join(self.Magisk_dir, 'magisk32'), 'magisk32.xz')
        else:
            self.SKIP32 = '#'
        if self.Magisk_dir and os.path.exists(os.path.join(self.Magisk_dir, 'magisk64')):
            self.exec('compress=xz', os.path.join(self.Magisk_dir, 'magisk64'), 'magisk64.xz')
        else:
            self.SKIP64 = '#'
        if self.Magisk_dir and os.path.exists(os.path.join(self.Magisk_dir, 'stub.apk')):
            self.exec('compress=xz', os.path.join(self.Magisk_dir, 'stub.apk'), 'stub.xz')
        else:
            self.SKIPSTUB = '#'
        if not self.Magisk_dir or not os.path.exists(os.path.join(self.Magisk_dir, 'magiskinit')):
            raise MagiskPatchError('Magisk patch assets do not contain magiskinit')
        self.exec(
            'cpio',
            'ramdisk.cpio',
            f"add 0750 {self.init} {os.path.join(self.Magisk_dir, 'magiskinit')}",
            'mkdir 0750 overlay.d',
            'mkdir 0750 overlay.d/sbin',
            f'{self.SKIP32} add 0644 overlay.d/sbin/magisk32.xz magisk32.xz',
            f'{self.SKIP64} add 0644 overlay.d/sbin/magisk64.xz magisk64.xz',
            f'{self.SKIPSTUB} add 0644 overlay.d/sbin/stub.xz stub.xz',
            'patch',
            f'{self.SKIPBACKUP} backup ramdisk.cpio.orig',
            'mkdir 000 .backup',
            'add 000 .backup/.magisk config',
        )
        for name in ('ramdisk.cpio.orig', 'config', 'magisk32.xz', 'magisk64.xz'):
            self.remove(name)
        for dt_name in ('dtb', 'kernel_dtb', 'extra'):
            if os.path.exists(os.path.join(self.local, dt_name)):
                self._emit(f'Patch fstab in {dt_name}')
                self.exec('dtb', dt_name, 'patch')

    def remove(self, file_):
        path = Path(file_)
        if not path.is_absolute():
            path = Path(self.local) / path
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file() or path.is_symlink():
            path.unlink()

    def patch_kernel(self):
        if os.path.exists(os.path.join(self.local, 'kernel')):
            self.exec(
                'hexpatch',
                'kernel',
                '49010054011440B93FA00F71E9000054010840B93FA00F7189000054001840B91FA00F7188010054',
                'A1020054011440B93FA00F7140020054010840B93FA00F71E0010054001840B91FA00F7181010054',
            )
            self.exec('hexpatch', 'kernel', '821B8012', 'E2FF8F12')
            self.exec('hexpatch', 'kernel', '736B69705F696E697472616D667300', '77616E745F696E697472616D667300')

    def repack(self):
        self._emit('Repacking boot image')
        result = self.exec('repack', self.boot_img)
        if result != 0:
            raise MagiskPatchError(f'Unable to repack boot image, magiskboot exit code: {result}')

    def extract_magisk(self):
        custom = os.path.join(self.local, 'custom')
        if os.path.exists(custom):
            shutil.rmtree(custom)
        os.makedirs(custom)
        if not self.MAGISKAPK or not os.path.exists(self.MAGISKAPK):
            raise FileNotFoundError(f'Magisk APK does not exist: {self.MAGISKAPK}')
        if not zipfile.is_zipfile(self.MAGISKAPK):
            raise MagiskPatchError(f'File is not a valid Magisk APK: {self.MAGISKAPK}')

        library_names = {
            'libmagisk64.so': 'magisk64',
            'libmagisk32.so': 'magisk32',
            'libmagiskinit.so': 'magiskinit',
        }
        with zipfile.ZipFile(self.MAGISKAPK) as archive:
            names = archive.namelist()
            architectures = [
                name.split('/')[1].strip()
                for name in names
                if name.startswith('lib/') and name.endswith('/libmagiskboot.so')
            ]
            selected_arch = self.PATCH_ARCH
            if not selected_arch:
                if len(architectures) != 1:
                    raise MagiskPatchError(
                        'Patch architecture must be selected explicitly. '
                        f'Available architectures: {", ".join(architectures) or "none"}'
                    )
                selected_arch = architectures[0]
            if selected_arch not in architectures:
                raise MagiskPatchError(
                    f'Architecture {selected_arch!r} is unavailable. '
                    f'Available architectures: {", ".join(architectures) or "none"}'
                )
            patch_arches = [arch for arch in architectures if selected_arch[:3] in arch]
            for patch_arch in patch_arches:
                for member in [
                    name for name in names
                    if patch_arch in name and os.path.basename(name).startswith('libmagisk')
                ]:
                    if os.path.basename(member) in {'libmagiskboot.so', 'libmagiskpolicy.so'}:
                        continue
                    archive.extract(member, custom)
                    source = os.path.join(custom, member)
                    destination = os.path.join(custom, os.path.basename(member))
                    if not os.path.exists(destination) or os.path.getsize(source) > os.path.getsize(destination):
                        shutil.copyfile(source, destination)
            if 'assets/stub.apk' in names:
                archive.extract('assets/stub.apk', path=custom)
                shutil.copyfile(os.path.join(custom, 'assets', 'stub.apk'), os.path.join(custom, 'stub.apk'))

        for directory_name in ('lib', 'assets'):
            directory = os.path.join(custom, directory_name)
            if os.path.exists(directory):
                shutil.rmtree(directory)
        for name in os.listdir(custom):
            source = os.path.join(custom, name)
            target_name = library_names.get(os.path.basename(name))
            if os.path.isfile(source) and target_name:
                shutil.move(source, os.path.join(custom, target_name))
        self.Magisk_dir = custom
        self.custom = True

    def cleanup(self):
        if self.custom and self.Magisk_dir and os.path.exists(self.Magisk_dir):
            shutil.rmtree(self.Magisk_dir)
        for name in ('kernel', 'kernel_dtb', 'ramdisk.cpio', 'stub.xz', 'stock_boot.img', 'dtb', 'extra'):
            self.remove(name)
        self.output = os.path.join(self.local, 'new-boot.img')

    def get_arch(self):
        if not self.MAGISKAPK or not zipfile.is_zipfile(self.MAGISKAPK):
            raise MagiskPatchError(f'File is not a valid Magisk APK: {self.MAGISKAPK}')
        with zipfile.ZipFile(self.MAGISKAPK) as archive:
            return [
                name.split('/')[1].strip()
                for name in archive.namelist()
                if name.startswith('lib/') and name.endswith('/libmagiskboot.so')
            ]

    @staticmethod
    def sha1(file_path):
        if not file_path or not os.path.exists(file_path):
            return ''
        with open(file_path, 'rb') as file_handle:
            return hashlib.sha1(file_handle.read()).hexdigest()


__all__ = ['MagiskPatchError', 'Magisk_patch', 'OutputSink']
