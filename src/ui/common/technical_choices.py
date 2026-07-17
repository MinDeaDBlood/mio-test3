from __future__ import annotations

from dataclasses import dataclass

from src.ui.localization import LocalizationCatalog
from src.ui.common import technical_choice_keys as keys


TECHNICAL_VALUE_KEYS: dict[str, str] = {
    "raw": keys.FORMAT_RAW_IMAGE,
    "sparse": keys.FORMAT_SPARSE_IMAGE,
    "dat": keys.FORMAT_DAT,
    "br": keys.FORMAT_BROTLI_DAT,
    "xz": keys.FORMAT_XZ_DAT,
    "new.dat": keys.FORMAT_DAT,
    "new.dat.br": keys.FORMAT_BROTLI_DAT,
    "new.dat.xz": keys.FORMAT_XZ_DAT,
    "img": keys.FORMAT_IMG,
    "payload": keys.FORMAT_PAYLOAD,
    "super": keys.FORMAT_SUPER,
    "update.app": keys.FORMAT_UPDATE_APP,
    "zst": keys.FORMAT_ZSTD,
    "zip": keys.FORMAT_ZIP,
    "ext": keys.FILESYSTEM_EXT4,
    "ext4": keys.FILESYSTEM_EXT4,
    "f2fs": keys.FILESYSTEM_F2FS,
    "erofs": keys.FILESYSTEM_EROFS,
    "boot": keys.IMAGE_BOOT,
    "recovery": keys.IMAGE_RECOVERY,
    "vendor_boot": keys.IMAGE_VENDOR_BOOT,
    "make_ext4fs": keys.PACKER_MAKE_EXT4FS,
    "mke2fs+e2fsdroid": keys.PACKER_MKE2FS_E2FSDROID,
    "lz4": keys.COMPRESSION_LZ4,
    "lz4hc": keys.COMPRESSION_LZ4HC,
    "lzma": keys.COMPRESSION_LZMA,
    "deflate": keys.COMPRESSION_DEFLATE,
    "zstd": keys.COMPRESSION_ZSTD,
    "qti_dynamic_partitions": keys.SUPER_GROUP_QTI_DYNAMIC,
    "main": keys.SUPER_GROUP_MAIN,
    "mot_dp_group": keys.SUPER_GROUP_MOTOROLA,
    "arm64-v8a": keys.ARCH_ARM64_V8A,
    "armeabi-v7a": keys.ARCH_ARMEABI_V7A,
    "x86": keys.ARCH_X86,
    "x86_64": keys.ARCH_X86_64,
    "utf-8": keys.ENCODING_UTF8,
    "gbk": keys.ENCODING_GBK,
    "gb2312": keys.ENCODING_GB2312,
    "utf-16": keys.ENCODING_UTF16,
    "B": keys.UNIT_B,
    "KB": keys.UNIT_KB,
    "MB": keys.UNIT_MB,
    "GB": keys.UNIT_GB,
    "TB": keys.UNIT_TB,
    "PB": keys.UNIT_PB,
    "KiB": keys.UNIT_KIB,
    "MiB": keys.UNIT_MIB,
    "GiB": keys.UNIT_GIB,
    "TiB": keys.UNIT_TIB,
    "EB": keys.UNIT_EB,
    "light": keys.THEME_LIGHT,
    "dark": keys.THEME_DARK,
    "Magisk": keys.MAGISK_NAME,
    "vbmeta": keys.VBMETA_NAME,
    "fs_config": keys.FS_CONFIG_NAME,
    "file_contexts": keys.FILE_CONTEXTS_NAME,
    "7z": keys.FILE_TYPE_7Z,
    "ozip": keys.FILE_TYPE_OZIP,
    "gpt": keys.FILE_TYPE_GPT,
    "splash": keys.FILE_TYPE_SPLASH,
    "dtbo": keys.FILE_TYPE_DTBO,
    "dtb": keys.FILE_TYPE_DTB,
    "exe": keys.FILE_TYPE_EXE,
    "elf": keys.FILE_TYPE_ELF,
    "avb_foot": keys.FILE_TYPE_AVB_FOOTER,
    "bzip2": keys.FILE_TYPE_BZIP2,
    "chrome": keys.FILE_TYPE_CHROMEOS,
    "gzip": keys.FILE_TYPE_GZIP,
    "lz4_legacy": keys.FILE_TYPE_LZ4_LEGACY,
    "zopfli": keys.FILE_TYPE_ZOPFLI,
    "lz4_lg": keys.FILE_TYPE_LZ4_LG,
    "png": keys.FILE_TYPE_PNG,
    "logo": keys.FILE_TYPE_LOGO,
    "rk_rsce": keys.FILE_TYPE_RK_RESOURCE,
    "kdz": keys.FILE_TYPE_KDZ,
    "dz": keys.FILE_TYPE_DZ,
    "macos_bin": keys.FILE_TYPE_MACOS_BINARY,
    "pac": keys.FILE_TYPE_PAC,
    "NTPI": keys.FILE_TYPE_NTPI,
    "amlogic": keys.FILE_TYPE_AMLOGIC,
    "romfs": keys.FILE_TYPE_ROMFS,
    "ubi": keys.FILE_TYPE_UBI,
    "squashfs": keys.FILE_TYPE_SQUASHFS,
    "jffs2": keys.FILE_TYPE_JFFS2,
    "rkfw": keys.FILE_TYPE_RKFW,
    "rkaf": keys.FILE_TYPE_RKAF,
    "guoke_logo": keys.FILE_TYPE_GUOKE_LOGO,
    "tar": keys.FILE_TYPE_TAR,
    "unknown": keys.FILE_TYPE_UNKNOWN,
    "empty": keys.FILE_TYPE_EMPTY,
    "fnf": keys.FILE_TYPE_FILE_NOT_FOUND,
    "fne": keys.FILE_TYPE_FILE_NOT_FOUND,
}


@dataclass(frozen=True)
class LocalizedChoiceSet:
    values: tuple[str, ...]
    labels: tuple[str, ...]

    def label_for(self, value: str) -> str:
        try:
            return self.labels[self.values.index(value)]
        except ValueError as exc:
            raise KeyError(f"Unsupported localized choice value: {value!r}") from exc

    def index_for(self, value: str) -> int:
        try:
            return self.values.index(value)
        except ValueError as exc:
            raise KeyError(f"Unsupported technical choice value: {value!r}") from exc

    def value_at(self, index: int) -> str:
        if index < 0 or index >= len(self.values):
            raise IndexError(f"Technical choice index is out of range: {index}")
        return self.values[index]

    def label_at(self, index: int) -> str:
        if index < 0 or index >= len(self.labels):
            raise IndexError(f"Technical choice label index is out of range: {index}")
        return self.labels[index]


def build_choice_set(
    texts: LocalizationCatalog,
    values: tuple[str, ...] | list[str],
) -> LocalizedChoiceSet:
    normalized = tuple(values)
    missing = [value for value in normalized if value not in TECHNICAL_VALUE_KEYS]
    if missing:
        raise KeyError(f"Missing technical localization keys for values: {missing!r}")
    labels = tuple(
        texts.resolve_required_ui_text(TECHNICAL_VALUE_KEYS[value])
        for value in normalized
    )
    if len(set(labels)) != len(labels):
        raise ValueError(
            f"Localized technical labels must be unique for values {normalized!r}: {labels!r}"
        )
    return LocalizedChoiceSet(values=normalized, labels=labels)


def technical_label(texts: LocalizationCatalog, value: str) -> str:
    return build_choice_set(texts, (value,)).labels[0]


__all__ = [
    "LocalizedChoiceSet",
    "TECHNICAL_VALUE_KEYS",
    "build_choice_set",
    "technical_label",
]
