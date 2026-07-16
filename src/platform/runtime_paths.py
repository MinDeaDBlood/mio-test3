from __future__ import annotations

from pathlib import Path

from src.core.paths import prog_path

PROJECT_ROOT = Path(prog_path)
BIN_DIR = PROJECT_ROOT / "bin"
CONFIG_DIR = PROJECT_ROOT / "config"
LANGUAGE_DIR = PROJECT_ROOT / "languages"
LICENSE_DIR = BIN_DIR / "licenses"
PLUGINS_DIR = PROJECT_ROOT / "plugins"
PLUGIN_DATABASE_FILE = PLUGINS_DIR / "plugin_db.json"
PLUGIN_INSTALL_DIR = PLUGINS_DIR / "installed"
TEMP_DIR = PROJECT_ROOT / "temp"
PLUGIN_TEMP_DIR = TEMP_DIR / "plugins"
PLUGIN_DOWNLOAD_DIR = PLUGIN_TEMP_DIR / "downloads"
PLUGIN_RUNTIME_DIR = PLUGIN_TEMP_DIR / "runtime"
UPDATE_TEMP_DIR = TEMP_DIR / "updates"
MAGISK_TEMP_DIR = TEMP_DIR / "magisk"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OTA_TEMPLATE_DIR = TEMPLATES_DIR / "ota"
MTK_PORT_TEMP_DIR = TEMP_DIR / "mtk_port"

SETTINGS_FILE = CONFIG_DIR / "settings.ini"
MTK_PORT_PROFILES_FILE = CONFIG_DIR / "mtk_port_profiles.json"
CONTEXT_RULES_FILE = CONFIG_DIR / "context_rules.json"
POSTINSTALL_TEMPLATE_FILE = OTA_TEMPLATE_DIR / "postinstall_config.txt"
UPDATE_BINARY_FILE = BIN_DIR / "update-binary"

__all__ = [
    "BIN_DIR",
    "CONFIG_DIR",
    "CONTEXT_RULES_FILE",
    "LANGUAGE_DIR",
    "LICENSE_DIR",
    "MTK_PORT_TEMP_DIR",
    "MAGISK_TEMP_DIR",
    "MTK_PORT_PROFILES_FILE",
    "OTA_TEMPLATE_DIR",
    "PLUGIN_DATABASE_FILE",
    "PLUGIN_DOWNLOAD_DIR",
    "PLUGIN_INSTALL_DIR",
    "PLUGIN_RUNTIME_DIR",
    "PLUGINS_DIR",
    "POSTINSTALL_TEMPLATE_FILE",
    "PROJECT_ROOT",
    "SETTINGS_FILE",
    "TEMP_DIR",
    "TEMPLATES_DIR",
    "UPDATE_BINARY_FILE",
    "UPDATE_TEMP_DIR",
]
