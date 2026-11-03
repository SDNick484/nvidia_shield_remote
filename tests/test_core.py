"""Tests for the Shield core library."""

import pathlib
from unittest.mock import MagicMock, call, patch

import pytest
from adb_shell.exceptions import AdbConnectionError, DeviceAuthError

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
    ShieldConfigError,
    ShieldConnectionError,
)


def test_escape_adb_text() -> None:
    assert escape_adb_text("") == ""
    assert escape_adb_text("hello world") == "hello%sworld"
    assert escape_adb_text("a b  c") == "a%sb%s%sc"
    assert escape_adb_text('echo "test"') == 'echo%s\\"test\\"'
    assert escape_adb_text("foo&bar;baz") == "foo\\&bar\\;baz"
    assert escape_adb_text("price $5") == "price%s\\$5"


def test_ensure_adb_key_generates_when_missing(tmp_path: pathlib.Path) -> None:
    key_file = tmp_path / "new_key"
    with patch("adb_shell.auth.keygen.keygen") as mock_keygen, \
         patch("adb_shell.auth.keygen.write_public_keyfile") as mock_write_pub:
        # Create key when keygen is called
        def fake_keygen(path: str) -> None:
            pathlib.Path(path).touch()
            pathlib.Path(path + ".pub").touch()

        mock_keygen.side_effect = fake_keygen
        result = ensure_adb_key(custom_key_path=key_file)
        assert result == key_file.resolve()
        mock_keygen.assert_called_once_with(str(key_file.resolve()))


def test_shield_init_no_host_raises() -> None:
    with patch("nvidia_shield_remote.core.resolve_shield_host", return_value=None):
        with pytest.raises(ShieldConfigError, match="Shield host/IP not specified"):
            Shield(auto_connect=True)


def test_shield_deprecated_alias(tmp_path: pathlib.Path) -> None:
    with pytest.deprecated_call():
        dev = shield(ip="127.0.0.1:5555", auto_connect=False)
        assert isinstance(dev, Shield)
        assert dev.host == "127.0.0.1"
        assert dev.port == 5555


def test_shield_buttons_contain_menu_and_mute() -> None:
    assert "menu" in DEFAULT_BUTTONS
    assert DEFAULT_BUTTONS["menu"] == "KEYCODE_MENU"
    assert "mute" in DEFAULT_BUTTONS
    assert DEFAULT_BUTTONS["mute"] == "KEYCODE_VOLUME_MUTE"


def test_shield_apps_contain_2026_services() -> None:
    assert "max" in DEFAULT_APPS
    assert "com.wbd.stream" in DEFAULT_APPS["max"]
    assert "music" in DEFAULT_APPS
    assert "youtube.music" in DEFAULT_APPS["music"]
    assert "paramount" in DEFAULT_APPS
    assert "fandango" in DEFAULT_APPS
    assert "peacock" in DEFAULT_APPS
    assert "appletv" in DEFAULT_APPS
    assert "jellyfin" in DEFAULT_APPS


@patch("nvidia_shield_remote.core.ensure_adb_key")
@patch("nvidia_shield_remote.core.PythonRSASigner.FromRSAKeyPath")
@patch("nvidia_shield_remote.core.AdbDeviceTcp")
def test_shield_connect_success(mock_adb_tcp: MagicMock, mock_signer: MagicMock, mock_key: MagicMock, tmp_path: pathlib.Path) -> None:
    mock_key.return_value = tmp_path / "adbkey"
    mock_instance = MagicMock()
    mock_instance.connect.return_value = True
    mock_instance.available = True
    mock_adb_tcp.return_value = mock_instance

    dev = Shield(host="192.168.1.50:5555", auto_connect=True)
    assert dev.is_connected()
    mock_instance.connect.assert_called_once()


@patch("nvidia_shield_remote.core.ensure_adb_key")
@patch("nvidia_shield_remote.core.PythonRSASigner.FromRSAKeyPath")
@patch("nvidia_shield_remote.core.AdbDeviceTcp")
def test_shield_connect_auth_failure(mock_adb_tcp: MagicMock, mock_signer: MagicMock, mock_key: MagicMock, tmp_path: pathlib.Path) -> None:
    mock_key.return_value = tmp_path / "adbkey"
    mock_instance = MagicMock()
    mock_instance.connect.side_effect = DeviceAuthError("Device rejected key")
    mock_adb_tcp.return_value = mock_instance

    with pytest.raises(ShieldAuthError, match="Shield authentication failed"):
        Shield(host="192.168.1.50:5555", auto_connect=True)


@patch("nvidia_shield_remote.core.ensure_adb_key")
@patch("nvidia_shield_remote.core.PythonRSASigner.FromRSAKeyPath")
@patch("nvidia_shield_remote.core.AdbDeviceTcp")
def test_shield_connect_network_failure(mock_adb_tcp: MagicMock, mock_signer: MagicMock, mock_key: MagicMock, tmp_path: pathlib.Path) -> None:
    mock_key.return_value = tmp_path / "adbkey"
    mock_instance = MagicMock()
    mock_instance.connect.side_effect = AdbConnectionError("Connection refused")
    mock_adb_tcp.return_value = mock_instance

    with pytest.raises(ShieldConnectionError, match="Could not connect to Shield"):
        Shield(host="192.168.1.50:5555", auto_connect=True)


def test_shield_press_valid_and_invalid() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    dev.shell = MagicMock(return_value="")  # type: ignore[method-assign]

    dev.press("home")
    dev.shell.assert_called_with("input keyevent KEYCODE_HOME")

    dev.press("menu")
    dev.shell.assert_called_with("input keyevent KEYCODE_MENU")

    dev.press("mute")
    dev.shell.assert_called_with("input keyevent KEYCODE_VOLUME_MUTE")

    with pytest.raises(ShieldButtonNotFoundError, match="Unknown button 'invalid_btn'"):
        dev.press("invalid_btn")


def test_shield_send_text() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    dev.shell = MagicMock(return_value="")  # type: ignore[method-assign]

    dev.send_text("Hello World!")
    dev.shell.assert_called_with("input text Hello%sWorld!")


def test_shield_shell_retry_on_disconnect() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    mock_device = MagicMock()
    # First call raises ConnectionResetError, second call succeeds
    mock_device.shell.side_effect = [ConnectionResetError("Socket reset"), "command output"]
    dev.device = mock_device
    dev._connected = True
    dev.connect = MagicMock()  # type: ignore[method-assign]

    out = dev.shell("echo 1")
    assert out == "command output"
    dev.connect.assert_called_once()
    assert mock_device.shell.call_count == 2


def test_shield_launch_with_monkey_fallback() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    dev.shell = MagicMock()  # type: ignore[method-assign]

    # 1. Success on am start
    dev.shell.return_value = "Starting: Intent { act=android.intent.action.MAIN ... }"
    dev.launch("netflix")
    dev.shell.assert_called_with("am start -n com.netflix.ninja/.MainActivity")

    # 2. am start reports error -> falls back to monkey
    dev.shell.side_effect = ["Error: Activity class does not exist.", "Events injected: 1"]
    dev.launch("max")
    assert dev.shell.call_args_list[-1] == call("monkey -p com.wbd.stream -c android.intent.category.LEANBACK_LAUNCHER 1")

    # 3. Package-only app launches directly via monkey
    dev.apps["custom"] = "org.custom.app"
    dev.shell.side_effect = ["Events injected: 1"]
    dev.launch("custom")
    assert dev.shell.call_args_list[-1] == call("monkey -p org.custom.app -c android.intent.category.LEANBACK_LAUNCHER 1")

    # 4. Unknown app raises ShieldAppNotFoundError
    with pytest.raises(ShieldAppNotFoundError, match="No such app 'unknown_app'"):
        dev.launch("unknown_app")


def test_shield_list_apps() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    dev.shell = MagicMock(return_value="""
  priority=0 match=0x108000
    ActivityInfo:
      name=com.netflix.ninja.MainActivity
      packageName=com.netflix.ninja
  priority=0 match=0x108000
    ActivityInfo:
      name=com.wbd.stream.MainActivity
      packageName=com.wbd.stream
""")  # type: ignore[method-assign]

    apps = dev.list_apps()
    assert apps == ["com.netflix.ninja", "com.wbd.stream"]


def test_shield_list_apps_fallback_pm_list() -> None:
    dev = Shield(host="192.168.1.50:5555", auto_connect=False)
    # First query returns empty, second returns pm list
    dev.shell = MagicMock(side_effect=["", "package:com.plexapp.android\npackage:org.xbmc.kodi\n"])  # type: ignore[method-assign]

    apps = dev.list_apps()
    assert apps == ["com.plexapp.android", "org.xbmc.kodi"]
