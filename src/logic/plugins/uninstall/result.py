"""Shared result contract for plugin removal operations."""

from __future__ import annotations

PluginUninstallResult = tuple[bool, str, list[str]]

__all__ = ['PluginUninstallResult']
