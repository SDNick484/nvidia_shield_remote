"""Configuration and path management for nvidia_shield_remote."""

from __future__ import annotations

import os
import pathlib
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


CONFIG_DIR_NAME = "nvidia-shield-remote"
CONFIG_FILE_NAME = "config.toml"
ENV_SHIELD_IP_PORT = "SHIELD_IP_PORT"


def get_config_dir() -> pathlib.Path:
    """Return the configuration directory path (~/.config/nvidia-shield-remote)."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = pathlib.Path(xdg_config).expanduser().resolve()
    else:
        base = (pathlib.Path.home() / ".config").resolve()
    return base / CONFIG_DIR_NAME


def get_config_path() -> pathlib.Path:
    """Return the path to the configuration file."""
    return get_config_dir() / CONFIG_FILE_NAME


def get_package_root() -> pathlib.Path:
    """Return the package root directory path."""
    return pathlib.Path(__file__).resolve().parent


def get_assets_dir() -> pathlib.Path:
    """Return the directory path containing GUI image assets."""
    package_assets = get_package_root() / "assets"
    if package_assets.is_dir():
        return package_assets
    # Fallback to repo root assets/ if running in non-packaged dev tree
    repo_assets = get_package_root().parent / "assets"
    if repo_assets.is_dir():
        return repo_assets
    return package_assets


def get_asset_path(filename: str) -> pathlib.Path:
    """Return the absolute path to a specific asset file."""
    return get_assets_dir() / filename


def _dump_toml(data: dict[str, Any]) -> str:
    """Simple, dependency-free TOML string serializer for primitive types and dict tables."""
    lines: list[str] = []
    # Write top-level key-values first
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_format_toml_val(value)}")

    # Write tables
    for section, table in data.items():
        if isinstance(table, dict):
            if lines:
                lines.append("")
            lines.append(f"[{section}]")
            for subkey, subval in table.items():
                lines.append(f"{subkey} = {_format_toml_val(subval)}")

    return "\n".join(lines) + "\n"


def _format_toml_val(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        items = ", ".join(_format_toml_val(x) for x in value)
        return f"[{items}]"
    return f'"{value}"'


def load_config(path: pathlib.Path | None = None) -> dict[str, Any]:
    """Load configuration from the specified path or the default config path."""
    config_path = path or get_config_path()
    if not config_path.is_file():
        return {}

    text = config_path.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            return tomllib.loads(text)
        except Exception:
            pass

    # Simple fallback parser for basic INI/TOML key = value and [section]
    result: dict[str, Any] = {}
    current_section: dict[str, Any] = result
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            sec_name = line[1:-1].strip()
            current_section = result.setdefault(sec_name, {})
        elif "=" in line:
            k, v = line.split("=", 1)
            key = k.strip()
            val = v.strip().strip('"').strip("'")
            current_section[key] = val
    return result


def save_config(data: dict[str, Any], path: pathlib.Path | None = None) -> pathlib.Path:
    """Save configuration data to the config file, creating parent directories if needed."""
    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    content = _dump_toml(data)
    config_path.write_text(content, encoding="utf-8")
    return config_path


def save_shield_host(host: str, path: pathlib.Path | None = None) -> pathlib.Path:
    """Save or update the Shield host/IP in the configuration file."""
    config = load_config(path)
    shield_section = config.setdefault("shield", {})
    shield_section["host"] = host
    return save_config(config, path)


def resolve_shield_host(cli_host: str | None = None, config_path: pathlib.Path | None = None) -> str | None:
    """Resolve Shield IP/host according to priority:
    1. CLI argument (--host / --ip)
    2. Environment variable (SHIELD_IP_PORT)
    3. Config file (~/.config/nvidia-shield-remote/config.toml)
    """
    if cli_host and cli_host.strip():
        return cli_host.strip()

    env_val = os.environ.get(ENV_SHIELD_IP_PORT)
    if env_val and env_val.strip():
        return env_val.strip()

    config = load_config(config_path)
    # Check [shield] host / ip / address
    shield_sec = config.get("shield", {})
    if isinstance(shield_sec, dict):
        host = shield_sec.get("host") or shield_sec.get("ip") or shield_sec.get("address")
        if host and str(host).strip():
            port = shield_sec.get("port")
            host_str = str(host).strip()
            if port and ":" not in host_str:
                return f"{host_str}:{port}"
            return host_str

    # Or top-level host/ip in config
    top_host = config.get("host") or config.get("ip") or config.get("SHIELD_IP_PORT")
    if top_host and str(top_host).strip():
        return str(top_host).strip()

    return None


def get_candidate_key_paths() -> list[pathlib.Path]:
    """Return the candidate ADB key paths in order of preference:
    1. ~/.android/adbkey
    2. ~/.config/nvidia-shield-remote/adbkey
    3. ./adbkey (current working directory fallback)
    """
    return [
        pathlib.Path.home() / ".android" / "adbkey",
        get_config_dir() / "adbkey",
        pathlib.Path.cwd() / "adbkey",
    ]


def locate_existing_adb_key() -> pathlib.Path | None:
    """Locate an existing ADB private key from the candidate paths.
    Checks that the private key exists and either a .pub file exists or can be read.
    """
    for candidate in get_candidate_key_paths():
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None
