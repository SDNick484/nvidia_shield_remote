"""Tests for CLI argument parsing, execution, and exit codes."""

from unittest.mock import MagicMock, patch

import pytest

from nvidia_shield_remote.cli import run_cli
from nvidia_shield_remote.exceptions import (
    ShieldAppNotFoundError,
    ShieldButtonNotFoundError,
    ShieldConnectionError,
)


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "CLI tool to control Nvidia Shield TV over ADB" in captured.out


def test_cli_list_commands(capsys: pytest.CaptureFixture[str]) -> None:
    # Must exit 0 and list commands without any connection attempt
    code = run_cli(["--list-commands"])
    assert code == 0
    captured = capsys.readouterr()
    assert "power" in captured.out
    assert "home" in captured.out
    assert "menu" in captured.out
    assert "mute" in captured.out


def test_cli_save_ip(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]) -> None:
    with patch("nvidia_shield_remote.cli.save_shield_host") as mock_save:
        mock_save.return_value = tmp_path / "config.toml"
        code = run_cli(["--save-ip", "192.168.1.200:5555"])
        assert code == 0
        mock_save.assert_called_once_with("192.168.1.200:5555")


def test_cli_no_action_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    code = run_cli([])
    assert code == 2
    captured = capsys.readouterr()
    assert "usage: shield-cli" in captured.err


def test_cli_unconfigured_host_error(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("nvidia_shield_remote.cli.resolve_shield_host", return_value=None):
        code = run_cli(["-c", "home"])
        assert code == 2
        captured = capsys.readouterr()
        assert "Error: Shield host/IP is not configured" in captured.err


@patch("nvidia_shield_remote.cli.Shield")
def test_cli_commands_sequence(mock_shield_cls: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_dev = MagicMock()
    mock_shield_cls.return_value = mock_dev

    # Test space-separated commands and repeated flags
    code = run_cli(["--ip", "192.168.1.50", "-c", "down", "center", "-c", "back"])
    assert code == 0
    assert mock_dev.press.call_count == 3
    mock_dev.press.assert_any_call("down")
    mock_dev.press.assert_any_call("center")
    mock_dev.press.assert_any_call("back")


@patch("nvidia_shield_remote.cli.Shield")
def test_cli_app_launch(mock_shield_cls: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_dev = MagicMock()
    mock_shield_cls.return_value = mock_dev

    code = run_cli(["--ip", "192.168.1.50", "-a", "netflix"])
    assert code == 0
    mock_dev.launch.assert_called_once_with("netflix")


@patch("nvidia_shield_remote.cli.Shield")
def test_cli_text_input(mock_shield_cls: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_dev = MagicMock()
    mock_shield_cls.return_value = mock_dev

    code = run_cli(["--ip", "192.168.1.50", "-t", "Stranger Things"])
    assert code == 0
    mock_dev.send_text.assert_called_once_with("Stranger Things")


@patch("nvidia_shield_remote.cli.Shield")
def test_cli_connection_error_exit_code(mock_shield_cls: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_shield_cls.side_effect = ShieldConnectionError("Device unreachable")

    code = run_cli(["--ip", "192.168.1.50", "-c", "home"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Connection error" in captured.err


@patch("nvidia_shield_remote.cli.Shield")
def test_cli_unknown_button_exit_code(mock_shield_cls: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    mock_dev = MagicMock()
    mock_dev.press.side_effect = ShieldButtonNotFoundError("Unknown button")
    mock_shield_cls.return_value = mock_dev

    code = run_cli(["--ip", "192.168.1.50", "-c", "bad_button"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Command error" in captured.err
