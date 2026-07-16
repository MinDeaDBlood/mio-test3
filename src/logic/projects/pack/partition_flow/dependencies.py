from __future__ import annotations

from src.core.extra import contextpatch, fspatch
from src.core.file_finder import findfile, remove_duplicate
from src.core.file_types import gettype
from src.core.json_store import JsonEdit
from src.core.logo import GuoKeLogo
from src.core.splash_editor import splash_repack
from src.core.vbmeta import Vbpatch
from src.logic.projects.common.cleanup_service import remove_packed_source
from src.logic.projects.dtbo.service import pack_dtbo
from src.logic.projects.logo.service import pack_logo
from src.logic.projects.pack.boot_images.service import repack_boot
from src.logic.projects.pack.filesystem_service import make_ext4fs, make_f2fs, mke2fs, mkerofs
from src.logic.projects.pack.registry import apply_output_format

from .service import PackPartitionDependencies


def build_default_pack_partition_dependencies() -> PackPartitionDependencies:
    """Build the concrete dependency bundle for the pack-partition workflow.

    Keeping this composition step outside the Tk window keeps the UI host focused
    on reading widget state and delegating work to the logic layer.
    """
    return PackPartitionDependencies(
        json_edit_cls=JsonEdit,
        fspatch_main=fspatch.main,
        contextpatch_main=contextpatch.main,
        contextpatch_scan_context=contextpatch.scan_context,
        guoke_logo_cls=GuoKeLogo,
        logo_pack_func=pack_logo,
        pack_dtbo_func=pack_dtbo,
        repack_boot_func=repack_boot,
        splash_repack_func=splash_repack,
        mkerofs_func=mkerofs,
        make_f2fs_func=make_f2fs,
        make_ext4fs_func=make_ext4fs,
        mke2fs_func=mke2fs,
        apply_output_format_func=apply_output_format,
        rdi_func=remove_packed_source,
        remove_duplicate_func=remove_duplicate,
        vbpatch_factory=Vbpatch,
        findfile_func=findfile,
        gettype_func=gettype,
    )


__all__ = ['build_default_pack_partition_dependencies']
