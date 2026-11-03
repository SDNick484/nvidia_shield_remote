"""Tests for GUI remote logic, worker threading, and keyboard bindings."""

import queue
import time
from unittest.mock import MagicMock, patch

import pytest

import nvidia_shield_remote.gui as gui_module
from nvidia_shield_remote.gui import RemoteGUI


class MockWidget:
    def __init__(self, *args, **kwargs):
        self.config_dict = {}
        self.grid_kwargs = {}

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def columnconfigure(self, col, **kwargs):
        pass

    def rowconfigure(self, row, **kwargs):
        pass

    def config(self, **kwargs):
        self.config_dict.update(kwargs)

    def insert(self, idx, text):
        self.text = text

    def get(self):
        return getattr(self, "text", "")


class MockTk(MockWidget):
    def __init__(self):
        super().__init__()
        self.bindings = {}
        self.protocols = {}

    def wm_title(self, title):
        self.title = title

    def minsize(self, w, h):
        pass

    def bind(self, seq, handler):
        self.bindings[seq] = handler

    def protocol(self, name, handler):
        self.protocols[name] = handler

    def after(self, ms, func):
        func()

    def destroy(self):
        pass


@pytest.fixture
def mock_tk():
    fake_tk = MagicMock()
    fake_tk.Tk = MockTk
    fake_tk.Frame = MockWidget
    fake_tk.Label = MockWidget
    fake_tk.Entry = MockWidget
    fake_tk.Button = MockWidget
    fake_tk.PhotoImage = MagicMock()
    fake_tk.FLAT = "flat"
    fake_tk.RAISED = "raised"

    with patch.object(gui_module, "tk", fake_tk):
        yield fake_tk


def test_gui_initialization_and_keybindings(mock_tk: MagicMock) -> None:
    root = MockTk()
    with patch("nvidia_shield_remote.gui.resolve_shield_host", return_value="192.168.1.99:5555"), \
         patch("nvidia_shield_remote.gui.Shield") as mock_shield_cls:
        mock_shield = MagicMock()
        mock_shield_cls.return_value = mock_shield

        remote = RemoteGUI(root, initial_host="192.168.1.99:5555")

        # Verify keyboard shortcuts are bound
        assert "<Up>" in root.bindings
        assert "<Down>" in root.bindings
        assert "<Left>" in root.bindings
        assert "<Right>" in root.bindings
        assert "<Return>" in root.bindings
        assert "<BackSpace>" in root.bindings
        assert "<Escape>" in root.bindings
        assert "<space>" in root.bindings
        assert "m" in root.bindings
        assert "h" in root.bindings
        assert "+" in root.bindings
        assert "-" in root.bindings

        # Clean shutdown worker thread
        remote._on_close()


def test_gui_key_triggers_send_press(mock_tk: MagicMock) -> None:
    root = MockTk()
    with patch("nvidia_shield_remote.gui.resolve_shield_host", return_value=None):
        remote = RemoteGUI(root, initial_host=None)
        remote.send_press = MagicMock()  # type: ignore[method-assign]

        fake_event = MagicMock()
        fake_event.widget = None

        # Trigger <Up> binding
        root.bindings["<Up>"](fake_event)
        remote.send_press.assert_called_with("up")

        # Trigger <space> binding
        root.bindings["<space>"](fake_event)
        remote.send_press.assert_called_with("play/pause")

        remote._on_close()


def test_gui_worker_processes_press(mock_tk: MagicMock) -> None:
    root = MockTk()
    with patch("nvidia_shield_remote.gui.Shield") as mock_shield_cls:
        mock_shield = MagicMock()
        mock_shield.is_connected.return_value = True
        mock_shield_cls.return_value = mock_shield

        remote = RemoteGUI(root, initial_host="192.168.1.99:5555")
        remote.shield = mock_shield

        # Put press action on queue
        remote.send_press("home")

        # Wait for queue to process
        remote.cmd_queue.join()

        mock_shield.press.assert_called_with("home")
        remote._on_close()
