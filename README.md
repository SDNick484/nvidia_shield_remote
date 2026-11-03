# Nvidia Shield Remote

A modern Python 3.10+ library, command-line interface, and responsive desktop remote GUI for controlling the NVIDIA Shield TV over ADB via TCP.

![Nvidia Shield Remote](assets/netflix_logo.png)

## Features

- **Pure Python ADB**: Powered by [`adb-shell`](https://github.com/JeffLIrion/adb-shell) — no external ADB binary or SDK tools required.
- **Automatic Key Management**: Automatically locates existing ADB keys (`~/.android/adbkey`, `~/.config/nvidia-shield-remote/adbkey`, `./adbkey`) or auto-generates a keypair and guides the first-time TV authorization prompt.
- **Hierarchical Configuration**: Resolves the Shield IP address via CLI flag &rarr; `SHIELD_IP_PORT` environment variable &rarr; `~/.config/nvidia-shield-remote/config.toml`.
- **Command-Line Interface (`shield-cli`)**: Execute single or chained button sequences (`-c down center`), send text input (`-t "Search Query"`), launch 2026 streaming services, or query installed Leanback apps.
- **Asynchronous Desktop GUI (`shield-remote`)**: Threaded, non-blocking Tkinter remote with connection status monitoring, in-app IP configuration, and full keyboard navigation.
- **Resilient App Launching**: Supports 2026 streaming services (Max, Netflix, Prime Video, Disney+, Apple TV+, Peacock, Paramount+, YouTube Music, Jellyfin, etc.) with automatic fallback to Android Leanback launcher activities.

---

## Prerequisites

1. **Python 3.10+**
2. **Enable Network Debugging on your Nvidia Shield**:
   - **Enable Developer Options**: Go to *Settings &rarr; Device Preferences &rarr; About &rarr; Build* and click *Build* 7 times until you see "You are now a developer".
   - **Enable Network Debugging**: Go to *Settings &rarr; Device Preferences &rarr; Developer Options &rarr; Network debugging* (toggle **ON**).
   - Note the IP address and port displayed (typically `<IP>:5555`).

---

## Installation

### Using pip
```bash
git clone https://github.com/SDNick484/nvidia_shield_remote.git
cd nvidia_shield_remote
pip install .
```

### For development / editable install
```bash
pip install -e ".[dev]"
```

### Using uv / pipx
```bash
uv tool install .
# or
pipx install .
```

---

## First-Time Pairing

When connecting for the first time:
1. Ensure your computer and Nvidia Shield are on the same local network.
2. Run any command or save your Shield IP:
   ```bash
   shield-cli --save-ip 192.168.1.130:5555 -c home
   ```
3. A prompt will appear on your TV screen: **"Allow USB/Network debugging?"**. Check **"Always allow from this computer"** and select **OK**.

---

## Configuration

Configuration resolution order:
1. `--ip <HOST[:PORT]>` CLI option
2. `SHIELD_IP_PORT` environment variable (e.g. `export SHIELD_IP_PORT="192.168.1.130:5555"`)
3. `~/.config/nvidia-shield-remote/config.toml`

### Permanent IP Configuration
You can save your Shield IP permanently using the CLI:
```bash
shield-cli --save-ip 192.168.1.130:5555
```
Or directly edit `~/.config/nvidia-shield-remote/config.toml`:
```toml
[shield]
host = "192.168.1.130:5555"

[apps]
# Optional custom app overrides (package/activity or package name)
plex = "com.plexapp.android/com.plexapp.plex.activities.SplashActivity"
jellyfin = "org.jellyfin.androidtv"
```

---

## CLI Usage (`shield-cli`)

```bash
# List available button commands (no connection required)
shield-cli --list-commands

# Send a single button command
shield-cli -c home

# Send multiple button commands in sequence
shield-cli -c down center
shield-cli -c down -c down -c center

# Launch streaming apps
shield-cli -a netflix
shield-cli -a max
shield-cli -a youtube

# Send text input to the active input field
shield-cli -t "The Matrix"

# List configured presets and query installed Leanback packages from TV
shield-cli --list-apps

# Override IP address on-the-fly
shield-cli --ip 192.168.1.140:5555 -c volume up
```

---

## Desktop GUI (`shield-remote`)

Launch the graphical remote control:
```bash
shield-remote
```
*(Or `python nvidia_remote.py` for backward compatibility)*

### GUI Features & Keyboard Shortcuts
- **Settings Bar**: View, edit, and save the target Shield IP:Port directly from the top bar.
- **Asynchronous Execution**: Background worker thread keeps the interface responsive without freezing during network calls.
- **Status Bar**: Real-time status indication (`Connected`, `Connecting...`, `Disconnected`).
- **Keyboard Shortcuts**:

| Key | Remote Action |
| --- | --- |
| `↑` `↓` `←` `→` (Arrows) | D-Pad Navigation |
| `Enter` / `Return` | OK / Center / Select |
| `Backspace` / `Escape` | Back |
| `Space` | Play / Pause |
| `m` / `M` | Mute |
| `+` / `=` | Volume Up |
| `-` | Volume Down |
| `h` / `H` | Home |

---

## Python API

You can import and use `Shield` programmatically in Python scripts:

```python
from nvidia_shield_remote import Shield

# Initializes and connects automatically
shield = Shield("192.168.1.130:5555")

# Navigation & controls
shield.press("home")
shield.press("menu")
shield.press("back")
shield.press("mute")

# Text input (auto-escapes whitespace and shell characters)
shield.send_text("Severance")

# App launching with automatic Leanback activity fallback
shield.launch("max")
shield.launch("netflix")

# Query installed Leanback packages
installed_apps = shield.list_apps()
print(installed_apps)
```

### Backward Compatibility
Legacy scripts importing `nvidia` and using `nvidia.shield` continue to function without modification:
```python
import nvidia

device = nvidia.shield("192.168.1.130:5555")
device.press("power")
```

---

## Running Tests

Run the full automated test suite with `pytest`:
```bash
pytest
```
