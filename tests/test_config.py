"""Tests for configuration and path resolution."""

import os
import pathlib
import tempfile
from unittest.mock import patch

import pytest

from nvidia_shield_remote.config import (
    ENV_SHIELD_IP_PORT,
    get_asset_path,
    get_assets_dir,
    get_candidate_key_paths,
    get_config_dir,
    get_config_path,
    load_config,
    locate_existing_adb_key,
    resolve_shield_host,
    save_config,
    save_shield_host,
)


def test_get_config_dir_custom_xdg(tmp_path: pathlib.Path) -> None:
    custom_xdg = tmp_path / "custom_xdg"
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(custom_xdg)}):
        cfg_dir = get_config_dir()
        assert cfg_dir == custom_xdg / "nvidia-shield-remote"


def test_load_and_save_config(tmp_path: pathlib.Path) -> None:
    cfg_file = tmp_path / "config.toml"
    assert load_config(cfg_file) == {}

    data = {
        "shield": {"host": "192.168.1.150:5555", "port": 5555},
        "apps": {"custom_app": "com.custom.app/.MainActivity"},
    }
    saved_path = save_config(data, cfg_file)
    assert saved_path == cfg_file
    assert cfg_file.is_file()

    loaded = load_config(cfg_file)
    assert loaded["shield"]["host"] == "192.168.1.150:5555"
    assert loaded["apps"]["custom_app"] == "com.custom.app/.MainActivity"


def test_save_shield_host(tmp_path: pathlib.Path) -> None:
    cfg_file = tmp_path / "config.toml"
    save_shield_host("10.0.0.99:5555", cfg_file)
    loaded = load_config(cfg_file)
    assert loaded["shield"]["host"] == "10.0.0.99:5555"


def test_resolve_shield_host_priority(tmp_path: pathlib.Path) -> None:
    cfg_file = tmp_path / "config.toml"
    save_config({"shield": {"host": "config-host:5555"}}, cfg_file)

    # 1. CLI arg takes highest priority
    with patch.dict(os.environ, {ENV_SHIELD_IP_PORT: "env-host:5555"}):
        res = resolve_shield_host("cli-host:5555", config_path=cfg_file)
        assert res == "cli-host:5555"

    # 2. Env variable takes second priority
    with patch.dict(os.environ, {ENV_SHIELD_IP_PORT: "env-host:5555"}):
        res = resolve_shield_host(None, config_path=cfg_file)
        assert res == "env-host:5555"

    # 3. Config file takes third priority
    with patch.dict(os.environ, {}, clear=True):
        res = resolve_shield_host(None, config_path=cfg_file)
        assert res == "config-host:5555"

    # 4. If nothing set, returns None
    empty_cfg = tmp_path / "empty.toml"
    with patch.dict(os.environ, {}, clear=True):
        res = resolve_shield_host(None, config_path=empty_cfg)
        assert res is None


def test_assets_paths() -> None:
    assets_dir = get_assets_dir()
    assert assets_dir.is_dir()

    netflix_png = get_asset_path("netflix_logo.png")
    assert netflix_png.is_file()
    assert netflix_png.name == "netflix_logo.png"


def test_locate_existing_adb_key(tmp_path: pathlib.Path) -> None:
    mock_key = tmp_path / "adbkey"
    mock_key.touch()

    with patch("nvidia_shield_remote.config.get_candidate_key_paths", return_value=[mock_key]):
        found = locate_existing_adb_key()
        assert found == mock_key.resolve()

    with patch("nvidia_shield_remote.config.get_candidate_key_paths", return_value=[tmp_path / "nonexistent"]):
        assert locate_existing_adb_key() is None
