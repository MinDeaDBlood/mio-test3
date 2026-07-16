from __future__ import annotations

import json
import logging
import os
import platform
import zipfile
from shutil import rmtree

from src.core.config_parser import ConfigParser
from src.logic.plugins.models import ModuleErrorCodes


class PluginInstallService:
    """Encapsulates plugin archive validation and installation.

    The UI and ``ModuleManager`` keep their public API stable, but the actual
    install lifecycle lives here so install logic is isolated from interface and
    orchestration concerns.
    """

    def __init__(self, *, module_dir: str, notify_plugin_state_changed, logger=None):
        self.module_dir = module_dir
        self.notify_plugin_state_changed = notify_plugin_state_changed
        self.logger = logger or logging

    @staticmethod
    def check_mpk(mpk):
        if not mpk or not os.path.exists(mpk) or not zipfile.is_zipfile(mpk):
            return ModuleErrorCodes.IsBroken, ''
        try:
            with zipfile.ZipFile(mpk) as f:
                f_list = f.namelist()
                if 'info' not in f_list:
                    return ModuleErrorCodes.IsBroken, 'Missing info file'
                if 'icon' not in f_list:
                    return ModuleErrorCodes.Normal, 'Missing icon file'
        except zipfile.BadZipFile:
            return ModuleErrorCodes.IsBroken, 'Corrupted MPK archive'
        return ModuleErrorCodes.Normal, ''

    def install(self, mpk_path):
        self.logger.info("PluginInstallService.install: starting installation from MPK: %s", mpk_path)
        check_mpk_result, reason = self.check_mpk(mpk_path)
        if check_mpk_result != ModuleErrorCodes.Normal:
            self.logger.error(
                "PluginInstallService.install: MPK check failed for %r. Result=%s Reason=%r",
                mpk_path,
                check_mpk_result,
                reason,
            )
            return check_mpk_result, reason

        mconf = ConfigParser()
        try:
            with zipfile.ZipFile(mpk_path) as f:
                with f.open('info') as info_file:
                    mconf.read_string(info_file.read().decode('utf-8'))
        except (OSError, UnicodeError, KeyError, zipfile.BadZipFile) as exc:
            self.logger.exception("PluginInstallService.install: error reading info from %r: %s", mpk_path, exc)
            return ModuleErrorCodes.IsBroken, 'Error reading MPK info file'

        install_id = mconf.get('module', 'identifier', None)
        if not install_id:
            return ModuleErrorCodes.IsBroken, 'Missing identifier in plugin info'

        supports_str = mconf.get('module', 'supports', '')
        supports = supports_str.split() if supports_str else []
        if supports and platform.system() not in supports:
            return ModuleErrorCodes.PlatformNotSupport, f'Unsupported platform: {platform.system()}'

        system_target = mconf.get('module', 'system', 'all')
        if system_target != 'all' and platform.system() not in system_target.split(' '):
            return ModuleErrorCodes.PlatformNotSupport, f'Unsupported platform: {system_target}'

        arch_target = mconf.get('module', 'arch', 'all')
        if arch_target != 'all' and platform.machine() not in arch_target.split(' '):
            return ModuleErrorCodes.ArchNotSupported, f'Unsupported Arch: {arch_target}'

        depend_str = mconf.get('module', 'depend', '')
        for dep_id_str in depend_str.split():
            if dep_id_str and not os.path.isdir(os.path.join(self.module_dir, dep_id_str)):
                return ModuleErrorCodes.DependsMissing, dep_id_str

        install_target_path = os.path.join(self.module_dir, install_id)
        if os.path.exists(install_target_path):
            try:
                rmtree(install_target_path)
                if os.path.exists(install_target_path):
                    return ModuleErrorCodes.GenericError, 'Failed to remove old version'
            except OSError as exc:
                self.logger.exception(
                    "PluginInstallService.install: error removing existing plugin dir %r: %s",
                    install_target_path,
                    exc,
                )
                return ModuleErrorCodes.GenericError, 'Error removing old version'

        resource_file_name_in_mpk = mconf.get('module', 'resource', None)
        if not resource_file_name_in_mpk:
            return ModuleErrorCodes.IsBroken, 'Missing resource field in plugin info'

        try:
            with zipfile.ZipFile(mpk_path, 'r') as mpk_zip_file_obj:
                if resource_file_name_in_mpk not in mpk_zip_file_obj.namelist():
                    return ModuleErrorCodes.IsBroken, 'Resource file specified in info not found in MPK'

                with mpk_zip_file_obj.open(resource_file_name_in_mpk, 'r') as inner_resource_zip_stream:
                    with zipfile.ZipFile(inner_resource_zip_stream, 'r') as resource_content_zip_obj:
                        os.makedirs(install_target_path, exist_ok=True)
                        resource_content_zip_obj.extractall(install_target_path)

                plugin_info_data = {n: v for n, v in mconf.items('module')}
                plugin_info_data['depend'] = depend_str

                info_json_target_path = os.path.join(install_target_path, 'info.json')
                with open(info_json_target_path, 'w', encoding='utf-8') as f_json:
                    json.dump(plugin_info_data, f_json, indent=2, ensure_ascii=False)

                if 'icon' in mpk_zip_file_obj.namelist():
                    icon_target_path = os.path.join(install_target_path, 'icon')
                    with open(icon_target_path, 'wb') as f_icon:
                        with mpk_zip_file_obj.open('icon') as icon_stream:
                            f_icon.write(icon_stream.read())
        except zipfile.BadZipFile as exc:
            self.logger.exception("PluginInstallService.install: bad ZIP for %r: %s", install_id, exc)
            return ModuleErrorCodes.IsBroken, 'Corrupted archive'
        except IOError as exc:
            self.logger.exception("PluginInstallService.install: IO error for %r: %s", install_id, exc)
            if os.path.exists(install_target_path):
                try:
                    rmtree(install_target_path)
                except OSError:
                    pass
            return ModuleErrorCodes.GenericError, f'IO Error: {exc}'
        except (RuntimeError, ValueError, KeyError) as exc:
            self.logger.exception("PluginInstallService.install: extraction error for %r: %s", install_id, exc)
            if os.path.exists(install_target_path):
                try:
                    rmtree(install_target_path)
                except OSError:
                    pass
            return ModuleErrorCodes.GenericError, f'Extraction error: {exc}'

        self.notify_plugin_state_changed(install_id)
        self.logger.info(
            "PluginInstallService.install: successfully installed plugin %r to %r",
            install_id,
            install_target_path,
        )
        return ModuleErrorCodes.Normal, ''


def install_plugin(module_manager, mpk_path: str):
    service = PluginInstallService(
        module_dir=module_manager.module_dir,
        notify_plugin_state_changed=module_manager.notify_plugin_state_changed,
        logger=logging,
    )
    return service.install(mpk_path)
