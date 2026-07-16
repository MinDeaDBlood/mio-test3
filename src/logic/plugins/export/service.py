from __future__ import annotations

import json
import logging
import os
import zipfile
from io import BytesIO, StringIO

from src.core.file_finder import get_all_file_paths
from src.core.config_parser import ConfigParser
from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput, build_service_output


class PluginExportService:
    """Builds MPK archives from installed plugins."""

    def __init__(
        self,
        *,
        module_dir: str,
        get_name,
        is_virtual,
        output_dir: str,
        output: ServiceOutput | None = None,
        logger=None,
    ):
        self.module_dir = module_dir
        self.get_name = get_name
        self.is_virtual = is_virtual
        self.output_dir = output_dir
        self.output = output or build_service_output()
        self.logger = logger or logging

    def export(self, plugin_id: str):
        name = self.get_name(plugin_id).replace('/', '')
        if self.is_virtual(plugin_id):
            self.output.report(
                message('plugin_export_virtual', '{name} is a virtual plugin', name=name),
                severity=OutputSeverity.WARNING,
            )
            return 1
        if not plugin_id:
            return 1

        plugin_dir_path = os.path.join(self.module_dir, plugin_id)
        info_json_path = os.path.join(plugin_dir_path, 'info.json')
        if not os.path.exists(info_json_path):
            self.output.report(
                message(
                    'plugin_export_metadata_missing',
                    'Plugin metadata is missing for {plugin_id}',
                    plugin_id=plugin_id,
                ),
                severity=OutputSeverity.ERROR,
            )
            return 2

        with open(info_json_path, 'r', encoding='UTF-8') as fh:
            data: dict = json.load(fh)
            data.setdefault('resource', 'main.zip')
            info_ini = ConfigParser()
            info_ini['module'] = data
            buffer_info_ini = StringIO()
            info_ini.write(buffer_info_ini)
            info_ini_content = buffer_info_ini.getvalue()
            buffer_info_ini.close()

        buffer_resource_zip = BytesIO()
        with zipfile.ZipFile(buffer_resource_zip, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as resource_zip_file:
            for item_path_abs in get_all_file_paths(plugin_dir_path):
                if os.path.basename(item_path_abs) in ['info.json', 'icon']:
                    continue
                arcname = os.path.relpath(item_path_abs, plugin_dir_path)
                self.output.log(message('plugin_export_adding_file', 'Adding file: {path}', path=arcname))
                try:
                    resource_zip_file.write(str(item_path_abs), arcname=arcname)
                except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
                    self.logger.exception('Error writing %s to resource zip', item_path_abs)
                    self.output.log(
                        message(
                            'plugin_export_add_failed',
                            'Cannot add file {path}: {error}',
                            path=item_path_abs,
                            error=exc,
                        ),
                        severity=OutputSeverity.ERROR,
                    )

        resource_zip_content = buffer_resource_zip.getvalue()
        buffer_resource_zip.close()
        output_mpk_path = os.path.join(self.output_dir, f'{name}.mpk')
        with zipfile.ZipFile(output_mpk_path, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as mpk_final_file:
            mpk_final_file.writestr(data['resource'], resource_zip_content)
            mpk_final_file.writestr('info', info_ini_content)
            icon_path = os.path.join(plugin_dir_path, 'icon')
            if os.path.exists(icon_path):
                mpk_final_file.write(icon_path, 'icon')

        if os.path.exists(output_mpk_path):
            self.output.report(
                message('plugin_export_complete', 'Plugin exported: {path}', path=output_mpk_path),
                severity=OutputSeverity.SUCCESS,
            )
        else:
            self.output.report(
                message('plugin_export_failed', 'Plugin export failed: {path}', path=output_mpk_path),
                severity=OutputSeverity.ERROR,
            )
        return None
