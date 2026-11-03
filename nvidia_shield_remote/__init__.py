"""Nvidia Shield Remote control library and CLI/GUI."""

from __future__ import annotations

from nvidia_shield_remote.config import (
    get_asset_path,
    get_assets_dir,
    get_config_dir,
    get_config_path,
    load_config,
    resolve_shield_host,
    save_config,
    save_shield_host,
)
from nvidia_shield_remote.core import (
    DEFAULT_APPS,
    DEFAULT_BUTTONS,
    Shield,
    ensure_adb_key,
    escape_adb_text,
    shield,
)
from nvidia_shield_remote.exceptions import (
    ShieldAppNotFoundError,
    ShieldAuthError,
    ShieldButtonNotFoundError,
    ShieldCommandError,
    ShieldConfigError,
    ShieldConnectionError,
    ShieldError,
)

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_APPS",
    "DEFAULT_BUTTONS",
    "Shield",
    "ShieldAppNotFoundError",
    "ShieldAuthError",
    "ShieldButtonNotFoundError",
    "ShieldCommandError",
    "ShieldConfigError",
    "ShieldConnectionError",
    "ShieldError",
    "ensure_adb_key",
    "escape_adb_text",
    "get_asset_path",
    "get_assets_dir",
    "get_config_dir",
    "get_config_path",
    "load_config",
    "resolve_shield_host",
    "save_config",
    "save_shield_host",
    "shield",
]
