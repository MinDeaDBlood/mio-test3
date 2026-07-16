from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

# Built-in profiles are domain defaults. Reading and writing user-editable JSON
# belongs to the application layer and is injected into MtkPortService.
_DEFAULT_SUPPORT_CHIPSET_PORTSTEP: dict[str, dict[str, Any]] = {
    "mt6572/mt6582/mt6592 kernel-3.4.67": {
        "partitions": {
            "system": "/dev/block/mmcblk0p4",
            "boot": "/dev/block/bootimg",
        },
        "flags": {
            "generate_script": True,
            "replace_kernel": True,
            "replace_fstab": False,
            "selinux_permissive": True,
            "enable_adb": True,
            "replace_firmware": True,
            "replace_mddb": True,
            "replace_malidriver": True,
            "replace_audiodriver": False,
            "replace_libshowlogo": False,
            "replace_mtk-kpd": True,
            "replace_gralloc": True,
            "replace_hwcomposer": True,
            "replace_ril": False,
            "single_simcard": False,
            "dual_simcard": False,
            "fit_density": True,
            "change_model": True,
            "change_timezone": True,
            "change_locale": True,
            "use_custom_update-binary": True,
        },
        "replace": {
            "kernel": ["kernel"],
            "fstab": [
                "initrd/fstab",
                "initrd/fstab.mt6572",
                "initrd/fstab.mt6582",
                "initrd/fstab.mt6592",
            ],
            "firmware": ["etc/firmware"],
            "mddb": ["etc/mddb"],
            "malidriver": ["lib/libMali.so"],
            "audiodriver": [
                "lib/libaudio.primary.default.so",
                "etc/audio_effects.conf",
                "etc/audio_policy.conf",
            ],
            "libshowlogo": ["lib/libshowlogo.so"],
            "mtk-kpd": ["usr/keylayout/mtk-kpd.kl"],
            "ril": [
                "bin/ccci_fsd",
                "bin/ccci_mdinit",
                "bin/gsm0710muxd",
                "bin/gsm0710muxdmd2 ",
                "bin/rild",
                "bin/rildmd2",
                "lib/librilmtk.so",
                "lib/librilmtkmd2.so",
                "lib/librilutils.so ",
                "lib/mtk-ril.so",
                "lib/mtk-rilmd2.so",
            ],
            "gralloc": [
                "lib/hw/gralloc.mt6572.so",
                "lib/hw/gralloc.mt6582.so",
                "lib/hw/gralloc.mt6592.so",
            ],
            "hwcomposer": [
                "lib/hw/hwcomposer.mt6572.so",
                "lib/hw/hwcomposer.mt6582.so",
                "lib/hw/hwcomposer.mt6592.so",
            ],
        },
    },
    "kernel only (only replace kernel)": {
        "partitions": {},
        "flags": {
            "generate_script": False,
            "replace_kernel": True,
            "selinux_permissive": True,
            "enable_adb": True,
            "replace_firmware": True,
            "replace_mddb": True,
        },
        "replace": {
            "kernel": ["kernel", "kernel.gz"],
            "firmware": ["etc/firmware"],
            "mddb": ["etc/mddb"],
        },
    },
    "G79 (mt6735/mt6735m/mt6737) kernel-3.18.19": {
        "partitions": {},
        "flags": {
            "generate_script": False,
            "replace_kernel": True,
            "replace_fstab": False,
            "selinux_permissive": True,
            "enable_adb": True,
            "replace_firmware": True,
            "replace_mddb": True,
            "replace_malidriver": False,
            "replace_audiodriver": False,
            "replace_libshowlogo": False,
            "replace_mtk-kpd": False,
            "replace_wifi": False,
            "replace_camera": False,
            "single_simcard": False,
            "dual_simcard": False,
            "fit_density": True,
            "change_model": True,
            "change_timezone": True,
            "change_locale": True,
            "use_custom_update-binary": True,
        },
        "replace": {
            "kernel": ["kernel"],
            "fstab": ["initrd/fstab", "initrd/fstab.mt6735", "initrd/fstab.mt6737"],
            "firmware": ["etc/firmware"],
            "mddb": ["etc/mddb"],
            "malidriver": ["lib/libMali.so"],
            "audiodriver": [
                "lib/hw/audio.primary.mt6735.so",
                "lib/hw/audio.primary.mt6735m.so",
                "lib/hw/audio.primary.mt6737.so",
                "lib/hw/audio.primary.mt6737m.so",
            ],
            "libshowlogo": ["lib/libshowlogo.so"],
            "mtk-kpd": ["usr/keylayout/mtk-kpd.kl"],
            "wifi": [
                "bin/netcfg",
                "bin/dhcpcd",
                "bin/ifconfig",
                "bin/hostap",
                "bin/hostapd",
                "bin/hostapd_bin",
                "bin/pcscd",
                "bin/wlan*",
                "bin/wpa*",
                "bin/netd",
                "lib/libhardware_legacy.so",
                "etc/wifi",
            ],
            "camera": [
                "lib/lib3a.so",
                "lib/libcamalgo.so",
                "lib/libcamdrv.so",
                "lib/libcameracustom.so",
                "lib/libfeatureio.so",
                "lib/libimageio.so",
                "lib/libimageio_plat_drv.so",
                "lib/libJpgDecPipe.so",
                "lib/libJpgEncPipe.so",
                "lib/libmhalImageCodec.so",
                "lib/libmtkcamera_client.so",
                "lib/libmtkjpeg.so",
                "lib/libcam.paramsmgr.so",
            ],
        },
    },
}


def default_support_chipset_profiles() -> dict[str, dict[str, Any]]:
    """Return an independent copy of the built-in MTK profile set."""

    return deepcopy(_DEFAULT_SUPPORT_CHIPSET_PORTSTEP)


def validate_support_chipset_profiles(data: object) -> dict[str, dict[str, Any]]:
    """Validate and copy profiles loaded by an external repository."""

    if not isinstance(data, Mapping):
        raise TypeError("MTK port profiles must be a mapping")

    profiles: dict[str, dict[str, Any]] = {}
    for raw_name, raw_profile in data.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise TypeError("MTK port profile names must be non-empty strings")
        if not isinstance(raw_profile, Mapping):
            raise TypeError(f"MTK port profile must be a mapping: {raw_name}")

        profile = dict(raw_profile)
        for section_name in ("flags", "replace", "partitions"):
            section = profile.get(section_name, {})
            if not isinstance(section, Mapping):
                raise TypeError(
                    f"MTK port profile section {section_name!r} must be a mapping: {raw_name}"
                )
            profile[section_name] = dict(section)
        profiles[raw_name] = deepcopy(profile)

    return profiles


__all__ = ["default_support_chipset_profiles", "validate_support_chipset_profiles"]
