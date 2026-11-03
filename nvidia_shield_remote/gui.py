"""Modern asynchronous Tkinter desktop remote GUI for Nvidia Shield TV."""

from __future__ import annotations

import logging
import queue
import sys
import threading
from typing import Any

from nvidia_shield_remote.config import (
    get_asset_path,
    resolve_shield_host,
    save_shield_host,
)
from nvidia_shield_remote.core import Shield
from nvidia_shield_remote.exceptions import (
    ShieldAppNotFoundError,
    ShieldAuthError,
    ShieldButtonNotFoundError,
    ShieldConnectionError,
    ShieldError,
)

logger = logging.getLogger(__name__)

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]


class RemoteGUI:
    """Tkinter-based GUI remote control for Nvidia Shield."""

    def __init__(self, root: Any, initial_host: str | None = None) -> None:
        if tk is None:
            raise RuntimeError("Tkinter is not installed on this system.")

        self.root = root
        self.root.wm_title("Nvidia Shield Remote")
        self.root.config(background="#121212")
        self.root.minsize(320, 680)

        self.shield: Shield | None = None
        self.cmd_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.is_connected = False
        self.current_host = initial_host or resolve_shield_host() or ""

        # Store image references to prevent Python GC collection
        self.image_refs: list[Any] = []

        self._build_ui()
        self._bind_keys()

        # Start worker thread
        self.worker_thread.start()

        # Auto-connect if host is configured
        if self.current_host:
            self.set_status("Connecting...", "#FF9800")
            self.cmd_queue.put(("connect", self.current_host))
        else:
            self.set_status("Disconnected (Configure Shield IP above)", "#E0E0E0")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        """Construct the remote layout and controls."""
        # Configure columns 0, 1, 2
        for col in range(3):
            self.root.columnconfigure(col, weight=1)

        # 1. Connection / Settings Bar (Row 0)
        conn_frame = tk.Frame(self.root, bg="#1E1E1E", bd=1, relief=tk.FLAT)
        conn_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=8)
        conn_frame.columnconfigure(1, weight=1)

        lbl = tk.Label(conn_frame, text="Shield IP:", fg="#CCCCCC", bg="#1E1E1E", font=("Helvetica", 9))
        lbl.grid(row=0, column=0, padx=(6, 4), pady=4)

        self.ip_entry = tk.Entry(conn_frame, font=("Helvetica", 9), bg="#2D2D2D", fg="#FFFFFF", insertbackground="#FFF")
        if self.current_host:
            self.ip_entry.insert(0, self.current_host)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        btn_connect = tk.Button(
            conn_frame,
            text="Connect",
            font=("Helvetica", 8, "bold"),
            bg="#2E7D32",
            fg="#FFFFFF",
            relief=tk.FLAT,
            command=self._on_connect_clicked,
        )
        btn_connect.grid(row=0, column=2, padx=4, pady=4)

        btn_save = tk.Button(
            conn_frame,
            text="Save",
            font=("Helvetica", 8),
            bg="#424242",
            fg="#FFFFFF",
            relief=tk.FLAT,
            command=self._on_save_clicked,
        )
        btn_save.grid(row=0, column=3, padx=(0, 6), pady=4)

        # Helper for creating remote buttons
        def make_btn(text: str, cmd_action: Any, width: int = 7, height: int = 2, bg: str = "#2A2A2A") -> tk.Button:
            return tk.Button(
                self.root,
                text=text,
                relief=tk.RAISED,
                borderwidth=1,
                font=("Helvetica", 9, "bold"),
                fg="#FFFFFF",
                bg=bg,
                activebackground="#3D3D3D",
                activeforeground="#FFFFFF",
                width=width,
                height=height,
                command=cmd_action,
            )

        # Row 1: Power, Back, Menu
        self.root.rowconfigure(1, weight=1)
        make_btn("Power", lambda: self.send_press("power"), bg="#8B0000").grid(row=1, column=0, padx=6, pady=4)
        make_btn("Back", lambda: self.send_press("back"), bg="#37474F").grid(row=1, column=1, padx=6, pady=4)
        make_btn("Menu", lambda: self.send_press("menu"), bg="#37474F").grid(row=1, column=2, padx=6, pady=4)

        # Row 2: Up
        self.root.rowconfigure(2, weight=1)
        make_btn("▲ Up", lambda: self.send_press("up"), height=1).grid(row=2, column=1, padx=6, pady=4)

        # Row 3: Left, Enter/Center, Right
        self.root.rowconfigure(3, weight=1)
        make_btn("◄ Left", lambda: self.send_press("left")).grid(row=3, column=0, padx=6, pady=4)
        make_btn("OK", lambda: self.send_press("center"), bg="#0288D1").grid(row=3, column=1, padx=6, pady=4)
        make_btn("Right ►", lambda: self.send_press("right")).grid(row=3, column=2, padx=6, pady=4)

        # Row 4: Down
        self.root.rowconfigure(4, weight=1)
        make_btn("▼ Down", lambda: self.send_press("down"), height=1).grid(row=4, column=1, padx=6, pady=4)

        # Row 5: Rewind, Play/Pause, Fast Forward
        self.root.rowconfigure(5, weight=1)
        make_btn("◄◄ Rew", lambda: self.send_press("rewind")).grid(row=5, column=0, padx=6, pady=4)
        make_btn("►/❚❚ Play", lambda: self.send_press("play/pause"), bg="#388E3C").grid(row=5, column=1, padx=6, pady=4)
        make_btn("FF ►►", lambda: self.send_press("ff")).grid(row=5, column=2, padx=6, pady=4)

        # Row 6: Vol Up, Mute, Vol Down
        self.root.rowconfigure(6, weight=1)
        make_btn("Vol +", lambda: self.send_press("volume up")).grid(row=6, column=0, padx=6, pady=4)
        make_btn("Mute", lambda: self.send_press("mute"), bg="#4E342E").grid(row=6, column=1, padx=6, pady=4)
        make_btn("Vol -", lambda: self.send_press("volume down")).grid(row=6, column=2, padx=6, pady=4)

        # Row 7: Home
        self.root.rowconfigure(7, weight=1)
        make_btn("Home", lambda: self.send_press("home"), bg="#E65100").grid(row=7, column=1, padx=6, pady=4)

        # App Launchers (Rows 8 to 13)
        app_list = [
            ("netflix", "netflix_logo.png", "Netflix"),
            ("hulu", "hulu_logo.png", "Hulu"),
            ("youtube", "youtube_logo.png", "YouTube"),
            ("youtubetv", "youtube_tv_logo.png", "YouTube TV"),
            ("vudu", "vudu_logo.png", "Vudu / Fandango"),
            ("disney", "disney_logo.png", "Disney+"),
        ]

        for idx, (app_name, asset_name, fallback_text) in enumerate(app_list, start=8):
            self.root.rowconfigure(idx, weight=1)
            img_path = get_asset_path(asset_name)
            app_btn = None
            if img_path.is_file():
                try:
                    img = tk.PhotoImage(file=str(img_path))
                    self.image_refs.append(img)
                    app_btn = tk.Button(
                        self.root,
                        image=img,
                        bg="#000000",
                        activebackground="#1E1E1E",
                        borderwidth=0,
                        highlightthickness=0,
                        command=lambda a=app_name: self.send_launch(a),
                    )
                except Exception as exc:
                    logger.debug("Could not load image %s: %s", img_path, exc)

            if app_btn is None:
                app_btn = tk.Button(
                    self.root,
                    text=fallback_text,
                    font=("Helvetica", 9, "bold"),
                    fg="#FFFFFF",
                    bg="#212121",
                    relief=tk.RAISED,
                    borderwidth=1,
                    width=18,
                    height=2,
                    command=lambda a=app_name: self.send_launch(a),
                )
            app_btn.grid(row=idx, column=1, pady=3)

        # Status Bar (Row 14)
        self.root.rowconfigure(14, weight=0)
        self.status_label = tk.Label(
            self.root,
            text="Status: Initializing...",
            font=("Helvetica", 9),
            bg="#000000",
            fg="#9E9E9E",
            anchor="w",
            padx=10,
            pady=4,
        )
        self.status_label.grid(row=14, column=0, columnspan=3, sticky="ew")

    def _bind_keys(self) -> None:
        """Register full keyboard shortcuts to window."""
        key_map = {
            "<Up>": "up",
            "<Down>": "down",
            "<Left>": "left",
            "<Right>": "right",
            "<Return>": "center",
            "<KP_Enter>": "center",
            "<BackSpace>": "back",
            "<Escape>": "back",
            "<space>": "play/pause",
            "m": "mute",
            "M": "mute",
            "h": "home",
            "H": "home",
            "+": "volume up",
            "=": "volume up",
            "<KP_Add>": "volume up",
            "-": "volume down",
            "_": "volume down",
            "<KP_Subtract>": "volume down",
        }

        for sequence, btn_name in key_map.items():
            self.root.bind(sequence, lambda event, b=btn_name: self._on_key(event, b))

    def _on_key(self, event: Any, button: str) -> None:
        """Handle keyboard key event if not typing into an entry widget."""
        if hasattr(event, "widget") and event.widget == self.ip_entry:
            return
        self.send_press(button)

    def _on_connect_clicked(self) -> None:
        """Handle click on Connect button."""
        new_host = self.ip_entry.get().strip()
        if not new_host:
            if messagebox:
                messagebox.showwarning("Missing IP", "Please enter Shield TV IP and port.")
            return
        self.current_host = new_host
        self.set_status(f"Connecting to {new_host}...", "#FF9800")
        self.cmd_queue.put(("connect", new_host))

    def _on_save_clicked(self) -> None:
        """Save the IP entered in the entry box to config.toml."""
        new_host = self.ip_entry.get().strip()
        if not new_host:
            if messagebox:
                messagebox.showwarning("Missing IP", "Please enter Shield TV IP to save.")
            return
        save_shield_host(new_host)
        self.current_host = new_host
        self.set_status(f"Saved IP: {new_host}", "#4CAF50")

    def send_press(self, button: str) -> None:
        """Queue a button press action asynchronously."""
        self.cmd_queue.put(("press", button))

    def send_launch(self, app: str) -> None:
        """Queue an app launch action asynchronously."""
        self.cmd_queue.put(("launch", app))

    def set_status(self, text: str, color: str = "#E0E0E0") -> None:
        """Thread-safe status bar update."""
        if threading.current_thread() is threading.main_thread():
            self.status_label.config(text=f"Status: {text}", fg=color)
        else:
            self.root.after(0, lambda: self.status_label.config(text=f"Status: {text}", fg=color))

    def _worker_loop(self) -> None:
        """Background thread executing ADB commands to prevent GUI freezes."""
        while True:
            item = self.cmd_queue.get()
            if item is None or item[0] == "stop":
                break

            action, payload = item
            try:
                if action == "connect":
                    host_to_connect = payload
                    if self.shield is not None:
                        self.shield.disconnect()
                    self.set_status(f"Connecting to {host_to_connect}...", "#FF9800")
                    self.shield = Shield(host=host_to_connect, auto_connect=True)
                    self.is_connected = True
                    self.set_status(f"Connected ({host_to_connect})", "#4CAF50")

                elif action == "press":
                    button = payload
                    if not self._ensure_shield_connected():
                        continue
                    assert self.shield is not None
                    self.shield.press(button)
                    self.set_status(f"Connected | Sent: {button}", "#4CAF50")

                elif action == "launch":
                    app = payload
                    if not self._ensure_shield_connected():
                        continue
                    assert self.shield is not None
                    self.set_status(f"Launching {app}...", "#FF9800")
                    self.shield.launch(app)
                    self.set_status(f"Connected | Launched: {app}", "#4CAF50")

            except ShieldAuthError as exc:
                self.is_connected = False
                self.set_status("Authentication Required (check TV screen)", "#F44336")
                logger.error("Shield auth error: %s", exc)
            except (ShieldConnectionError, ConnectionError, OSError) as exc:
                self.is_connected = False
                self.set_status("Disconnected (connection lost)", "#F44336")
                logger.error("Shield connection error: %s", exc)
            except ShieldButtonNotFoundError:
                self.set_status(f"Unknown button: {payload}", "#FF9800")
            except ShieldAppNotFoundError:
                self.set_status(f"App not found: {payload}", "#FF9800")
            except Exception as exc:
                self.set_status(f"Error: {exc}", "#F44336")
                logger.exception("Unexpected error in worker: %s", exc)
            finally:
                self.cmd_queue.task_done()

    def _ensure_shield_connected(self) -> bool:
        """Check if connected; if not, attempt to connect."""
        if self.shield and self.shield.is_connected():
            return True

        host = self.current_host or resolve_shield_host()
        if not host:
            self.set_status("Disconnected (set IP and click Connect)", "#F44336")
            return False

        self.set_status("Reconnecting...", "#FF9800")
        try:
            self.shield = Shield(host=host, auto_connect=True)
            self.is_connected = True
            self.set_status(f"Connected ({host})", "#4CAF50")
            return True
        except Exception as exc:
            self.is_connected = False
            self.set_status(f"Disconnected ({exc})", "#F44336")
            return False

    def _on_close(self) -> None:
        """Handle window close."""
        self.cmd_queue.put(("stop", None))
        if self.shield:
            try:
                self.shield.disconnect()
            except Exception:
                pass
        self.root.destroy()


def run_gui(host: str | None = None) -> None:
    """Launch the Remote GUI application."""
    if tk is None:
        print(
            "Error: Tkinter is required for the desktop remote GUI, but is not installed.\n"
            "Please install python3-tk (e.g. 'sudo apt install python3-tk' or package manager equivalent).",
            file=sys.stderr,
        )
        sys.exit(1)

    root = tk.Tk()
    RemoteGUI(root, initial_host=host)
    root.mainloop()


def main() -> None:
    """GUI entry point."""
    run_gui()


if __name__ == "__main__":
    main()
