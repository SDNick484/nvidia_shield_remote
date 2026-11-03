"""Exceptions for nvidia_shield_remote."""

from __future__ import annotations


class ShieldError(Exception):
    """Base exception for all Shield remote errors."""


class ShieldConnectionError(ShieldError):
    """Raised when connecting or communicating with the Shield fails."""


class ShieldAuthError(ShieldConnectionError):
    """Raised when ADB authentication or key authorization fails."""


class ShieldCommandError(ShieldError):
    """Raised when an ADB shell command fails on the Shield."""


class ShieldButtonNotFoundError(ShieldCommandError, KeyError):
    """Raised when an unknown button name is specified."""


class ShieldAppNotFoundError(ShieldCommandError, KeyError):
    """Raised when an unknown app name is specified."""


class ShieldConfigError(ShieldError):
    """Raised when configuration is missing or invalid."""
