"""Backward compatibility module for nvidia.py."""

from __future__ import annotations

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

buttons = Shield.buttons
apps = Shield.apps

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
    "apps",
    "buttons",
    "ensure_adb_key",
    "escape_adb_text",
    "shield",
]
