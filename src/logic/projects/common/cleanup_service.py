from __future__ import annotations

import logging
import os

from src.logic.common.messages import message
from src.logic.common.service_output import OutputSeverity, ServiceOutput, build_service_output
from src.logic.projects.common.workspace_service import rmdir


def remove_packed_source(
    work: str,
    part_name: str,
    *,
    listdir_func=os.listdir,
    access_func=os.access,
    remove_func=os.remove,
    remove_tree_func=rmdir,
    output: ServiceOutput | None = None,
) -> bool:
    output = output or build_service_output()
    config_dir = os.path.join(work, 'config')
    if os.path.isdir(config_dir) and not listdir_func(config_dir):
        return remove_tree_func(config_dir, quiet=True, output=output) == 0
    image_path = os.path.join(work, f'{part_name}.img')
    if not access_func(image_path, os.F_OK):
        output.report(message('operation_failed', 'Operation failed: {item}', item=part_name), severity=OutputSeverity.ERROR)
        return False
    output.log(message('removing', 'Removing {item}', item=part_name))
    try:
        if remove_tree_func(os.path.join(work, part_name), quiet=True, output=output) != 0:
            return False
        for pattern in ('%s_size.txt', '%s_file_contexts', '%s_fs_config', '%s_fs_options'):
            path = os.path.join(config_dir, pattern % part_name)
            if access_func(path, os.F_OK):
                remove_func(path)
    except OSError:
        logging.exception('Failed to remove %s', part_name)
        return False
    output.log(message('created', 'Created: {item}', item=part_name))
    return True


__all__ = ['remove_packed_source']
