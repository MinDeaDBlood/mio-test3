from __future__ import annotations

TITLE = "tools_view_title"
DOWNLOAD_FIRMWARE_BUTTON = "tools_toolbox_download_firmware_button"
GET_FILE_INFO_BUTTON = "tools_toolbox_get_file_info_button"
BYTE_CALCULATOR_BUTTON = "tools_toolbox_byte_calculator_button"
ALLOW_SELINUX_AUDIT_BUTTON = "tools_toolbox_allow_selinux_audit_button"
DISABLE_AVB_BUTTON = "tools_toolbox_disable_avb_button"
DISABLE_ENCRYPTION_BUTTON = "tools_toolbox_disable_encryption_button"
TRIM_RAW_IMAGE_BUTTON = "tools_toolbox_trim_raw_image_button"
MAGISK_PATCH_BUTTON = "tools_toolbox_magisk_patch_button"
MERGE_QUALCOMM_IMAGE_BUTTON = "tools_toolbox_merge_qualcomm_image_button"
MERGE_SUPER_BUTTON = "tools_toolbox_merge_super_button"
SPLIT_SUPER_BUTTON = "tools_toolbox_split_super_button"
DECRYPT_XTC_XML_BUTTON = "tools_toolbox_decrypt_xtc_xml_button"
MTK_PORT_BUTTON = "tools_toolbox_mtk_port_button"

__all__ = [name for name in globals() if name.isupper()]
