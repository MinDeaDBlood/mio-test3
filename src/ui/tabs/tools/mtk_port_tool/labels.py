from __future__ import annotations

from src.ui.tabs.tools.mtk_port_tool import keys


PROFILE_LABEL_KEYS: dict[str, str] = {
    "mt6572/mt6582/mt6592 kernel-3.4.67": keys.PROFILE_MT6572_MT6582_MT6592,
    "kernel only (only replace kernel)": keys.PROFILE_KERNEL_ONLY,
    "G79 (mt6735/mt6735m/mt6737) kernel-3.18.19": keys.PROFILE_G79,
}

FLAG_LABEL_KEYS: dict[str, str] = {
    "generate_script": keys.FLAG_GENERATE_SCRIPT,
    "replace_kernel": keys.FLAG_REPLACE_KERNEL,
    "replace_fstab": keys.FLAG_REPLACE_FSTAB,
    "selinux_permissive": keys.FLAG_SELINUX_PERMISSIVE,
    "enable_adb": keys.FLAG_ENABLE_ADB,
    "replace_firmware": keys.FLAG_REPLACE_FIRMWARE,
    "replace_mddb": keys.FLAG_REPLACE_MDDB,
    "replace_malidriver": keys.FLAG_REPLACE_MALI_DRIVER,
    "replace_audiodriver": keys.FLAG_REPLACE_AUDIO_DRIVER,
    "replace_libshowlogo": keys.FLAG_REPLACE_LIBSHOWLOGO,
    "replace_mtk-kpd": keys.FLAG_REPLACE_MTK_KEYPAD,
    "replace_gralloc": keys.FLAG_REPLACE_GRALLOC,
    "replace_hwcomposer": keys.FLAG_REPLACE_HWCOMPOSER,
    "replace_ril": keys.FLAG_REPLACE_RIL,
    "single_simcard": keys.FLAG_SINGLE_SIM,
    "dual_simcard": keys.FLAG_DUAL_SIM,
    "fit_density": keys.FLAG_FIT_DENSITY,
    "change_model": keys.FLAG_CHANGE_MODEL,
    "change_timezone": keys.FLAG_CHANGE_TIMEZONE,
    "change_locale": keys.FLAG_CHANGE_LOCALE,
    "use_custom_update-binary": keys.FLAG_CUSTOM_UPDATE_BINARY,
    "replace_wifi": keys.FLAG_REPLACE_WIFI,
    "replace_camera": keys.FLAG_REPLACE_CAMERA,
}


__all__ = ["FLAG_LABEL_KEYS", "PROFILE_LABEL_KEYS"]
