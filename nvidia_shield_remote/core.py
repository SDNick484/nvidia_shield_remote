"""Core library for controlling Nvidia Shield TV over ADB."""

from __future__ import annotations

import logging
import os
import pathlib
import re
import warnings
from typing import Any, Callable

from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth import keygen
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.exceptions import (
    AdbConnectionError,
    AdbTimeoutError,
    DeviceAuthError,
)

from nvidia_shield_remote.config import (
    get_config_dir,
    load_config,
    locate_existing_adb_key,
    resolve_shield_host,
)
from nvidia_shield_remote.exceptions import (
    ShieldAppNotFoundError,
    ShieldAuthError,
    ShieldButtonNotFoundError,
    ShieldCommandError,
    ShieldConfigError,
    ShieldConnectionError,
)

logger = logging.getLogger(__name__)

DEFAULT_BUTTONS: dict[str, str] = {
    "power": "KEYCODE_POWER",
    "sleep": "KEYCODE_SLEEP",
    "wake": "KEYCODE_WAKEUP",
    "home": "KEYCODE_HOME",
    "back": "KEYCODE_BACK",
    "menu": "KEYCODE_MENU",
    "mute": "KEYCODE_VOLUME_MUTE",
    "search": "KEYCODE_SEARCH",
    "up": "KEYCODE_DPAD_UP",
    "down": "KEYCODE_DPAD_DOWN",
    "left": "KEYCODE_DPAD_LEFT",
    "right": "KEYCODE_DPAD_RIGHT",
    "center": "KEYCODE_DPAD_CENTER",
    "enter": "KEYCODE_DPAD_CENTER",
    "select": "KEYCODE_DPAD_CENTER",
    "volume up": "KEYCODE_VOLUME_UP",
    "vol up": "KEYCODE_VOLUME_UP",
    "volume down": "KEYCODE_VOLUME_DOWN",
    "vol down": "KEYCODE_VOLUME_DOWN",
    "rewind": "KEYCODE_MEDIA_REWIND",
    "ff": "KEYCODE_MEDIA_FAST_FORWARD",
    "play/pause": "KEYCODE_MEDIA_PLAY_PAUSE",
    "play": "KEYCODE_MEDIA_PLAY_PAUSE",
    "pause": "KEYCODE_MEDIA_PLAY_PAUSE",
    "previous": "KEYCODE_MEDIA_PREVIOUS",
    "next": "KEYCODE_MEDIA_NEXT",
}

DEFAULT_APPS: dict[str, str] = {
    # Modern / updated 2026 streaming services & leanback targets
    "max": "com.wbd.stream/com.wbd.stream.MainActivity",
    "hbo": "com.wbd.stream/com.wbd.stream.MainActivity",  # backward compatibility alias
    "prime": "com.amazon.amazonvideo.livingroom/com.amazon.ignition.IgnitionActivity",
    "netflix": "com.netflix.ninja/.MainActivity",
    "youtube": "com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity",
    "youtubetv": "com.google.android.youtube.tvunplugged/com.google.android.apps.youtube.tvunplugged.activity.MainActivity",
    "music": "com.google.android.apps.youtube.music.tv",  # YouTube Music (replaces Google Play Music)
    "youtubemusic": "com.google.android.apps.youtube.music.tv",
    "disney": "com.disney.disneyplus/com.bamtechmedia.dominguez.main.MainActivity",
    "hulu": "com.hulu.livingroomplus/.WKFactivity",
    "apple": "com.apple.atve.androidtv.appletv/.MainActivity",
    "appletv": "com.apple.atve.androidtv.appletv/.MainActivity",
    "peacock": "com.peacocktv.peacockandroid/.activity.LeanbackMainActivity",
    "paramount": "com.cbs.ott/com.cbs.app.tv.ui.activity.SplashActivity",
    "cbs": "com.cbs.ott/com.cbs.app.tv.ui.activity.SplashActivity",  # CBS / Paramount+
    "vudu": "air.com.vudu.air.DownloaderTablet/.TvMainActivity",
    "fandango": "air.com.vudu.air.DownloaderTablet/.TvMainActivity",  # Fandango at Home (formerly Vudu)
    "jellyfin": "org.jellyfin.androidtv/.ui.startup.StartupActivity",
    "plex": "com.plexapp.android/com.plexapp.plex.activities.SplashActivity",
    "kodi": "org.xbmc.kodi/.Splash",
    "twitch": "tv.twitch.android.app/tv.twitch.android.apps.TwitchActivity",
    "spotify": "com.spotify.tv.android/.SpotifyTVActivity",
    "amazonmusic": "com.amazon.music.tv/.activity.MainActivity",
    "pandora": "com.pandora.android.atv/com.pandora.android.MainActivity",
    "ted": "com.ted.android.tv/.view.MainActivity",
    "pbs": "com.pbs.video/.ui.main.activities.StartupActivity",
    "games": "com.nvidia.tegrazone3/com.nvidia.tegrazone.leanback.LBMainActivity",
}


def escape_adb_text(text: str) -> str:
    r"""Escape text string for Android ADB 'input text' command.

    Android input text treats '%s' as whitespace, and characters such as
    spaces, backslashes, quotes, ampersands, semicolons, and parentheses
    must be escaped for the adb shell invocation.
    """
    if not text:
        return ""

    escaped_chars: list[str] = []
    # Shell metacharacters that must be escaped
    meta = set(r'''\"'`$&;()<>|*~[]{}''')

    for char in text:
        if char == " ":
            escaped_chars.append("%s")
        elif char in meta:
            escaped_chars.append(f"\\{char}")
        else:
            escaped_chars.append(char)

    return "".join(escaped_chars)


def ensure_adb_key(custom_key_path: str | pathlib.Path | None = None) -> pathlib.Path:
    """Locate an existing ADB key pair, or automatically generate one.

    Locations checked in order:
    1. custom_key_path (if provided)
    2. ~/.android/adbkey
    3. ~/.config/nvidia-shield-remote/adbkey
    4. ./adbkey (cwd fallback)

    If none exist, generates a keypair at ~/.config/nvidia-shield-remote/adbkey.
    """
    if custom_key_path:
        key_path = pathlib.Path(custom_key_path).expanduser().resolve()
        if not key_path.is_file():
            # If specified custom key does not exist, generate it
            key_path.parent.mkdir(parents=True, exist_ok=True)
            keygen.keygen(str(key_path))
        pub_path = pathlib.Path(str(key_path) + ".pub")
        if not pub_path.is_file():
            keygen.write_public_keyfile(str(key_path), str(pub_path))
        return key_path

    existing = locate_existing_adb_key()
    if existing:
        pub_path = pathlib.Path(str(existing) + ".pub")
        if not pub_path.is_file():
            try:
                keygen.write_public_keyfile(str(existing), str(pub_path))
            except Exception as exc:
                logger.warning("Could not write public key for %s: %s", existing, exc)
        return existing

    # Generate new key in ~/.config/nvidia-shield-remote/adbkey
    default_dir = get_config_dir()
    default_dir.mkdir(parents=True, exist_ok=True)
    new_key = default_dir / "adbkey"
    logger.info("No ADB key found; generating new keypair at %s", new_key)
    keygen.keygen(str(new_key))
    pub_path = pathlib.Path(str(new_key) + ".pub")
    if not pub_path.is_file():
        keygen.write_public_keyfile(str(new_key), str(pub_path))
    return new_key


class Shield:
    """Controller for Nvidia Shield TV via ADB over TCP."""

    buttons: dict[str, str] = DEFAULT_BUTTONS.copy()
    apps: dict[str, str] = DEFAULT_APPS.copy()

    def __init__(
        self,
        ip: str | bytes | None = None,
        port: int = 5555,
        *,
        host: str | None = None,
        key_path: str | pathlib.Path | None = None,
        timeout: float = 10.0,
        auto_connect: bool = True,
        app_overrides: dict[str, str] | None = None,
        auth_callback: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the Shield controller.

        :param ip: Shield IP address or host:port (str or bytes).
        :param port: Shield ADB port (default 5555).
        :param host: Optional alternative name for ip parameter.
        :param key_path: Explicit path to ADB private key.
        :param timeout: ADB connection and socket timeout in seconds.
        :param auto_connect: Whether to connect immediately upon initialization.
        :param app_overrides: Optional dictionary of app name to launch activity/package.
        :param auth_callback: Optional callback invoked when device requires user approval.
        """
        # Resolve target host/ip
        target = ip or host
        if isinstance(target, bytes):
            target = target.decode("utf-8")

        resolved = resolve_shield_host(target)
        if resolved:
            if ":" in resolved:
                parts = resolved.split(":", 1)
                self.host = parts[0]
                try:
                    self.port = int(parts[1])
                except ValueError:
                    self.port = port
            else:
                self.host = resolved
                self.port = port
        else:
            self.host = ""
            self.port = port

        self.shield_ip_and_port = f"{self.host}:{self.port}".encode("utf-8") if self.host else b""
        self.key_path = key_path
        self.timeout = timeout
        self.auth_callback = auth_callback
        self.device: AdbDeviceTcp | None = None
        self._connected = False

        # Apply app overrides from config file and parameter
        self.apps = DEFAULT_APPS.copy()
        config_data = load_config()
        config_apps = config_data.get("apps", {})
        if isinstance(config_apps, dict):
            for k, v in config_apps.items():
                self.apps[str(k).lower()] = str(v)
        if app_overrides:
            for k, v in app_overrides.items():
                self.apps[str(k).lower()] = str(v)

        if auto_connect:
            if not self.host:
                raise ShieldConfigError(
                    "Shield host/IP not specified. Provide via argument, SHIELD_IP_PORT environment variable, "
                    "or config.toml."
                )
            self.connect()

    def _default_auth_callback(self) -> None:
        """Invoked when the Shield displays the RSA authorization prompt."""
        logger.warning(
            "ADB authorization prompt displayed on Shield. Please check your TV screen and select "
            "'Always allow from this computer'."
        )
        print(
            "\n>>> ADB prompt: Please check your Nvidia Shield screen and select "
            "'Always allow from this computer' <<<\n"
        )
        if self.auth_callback:
            try:
                self.auth_callback()
            except Exception as exc:
                logger.error("Error in auth_callback: %s", exc)

    def connect(self) -> bool:
        """Establish connection to the Nvidia Shield via ADB TCP."""
        if not self.host:
            raise ShieldConfigError("Shield IP/host is not configured.")

        try:
            key_file = ensure_adb_key(self.key_path)
            signer = PythonRSASigner.FromRSAKeyPath(str(key_file))

            self.device = AdbDeviceTcp(
                self.host,
                self.port,
                default_transport_timeout_s=self.timeout,
            )
            success = self.device.connect(
                rsa_keys=[signer],
                auth_timeout_s=self.timeout,
                auth_callback=self._default_auth_callback,
            )
            self._connected = bool(success)
            if not success:
                raise ShieldAuthError(
                    f"Failed to authenticate with Shield at {self.host}:{self.port}. "
                    "Please check if network debugging is enabled and accept the RSA prompt on your TV."
                )
            return True
        except (DeviceAuthError, ShieldAuthError) as exc:
            self._connected = False
            raise ShieldAuthError(f"Shield authentication failed: {exc}") from exc
        except (AdbConnectionError, AdbTimeoutError, ConnectionError, OSError) as exc:
            self._connected = False
            raise ShieldConnectionError(
                f"Could not connect to Shield at {self.host}:{self.port}: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Close the active ADB connection."""
        if self.device is not None:
            try:
                self.device.close()
            except Exception:
                pass
        self._connected = False

    def is_connected(self) -> bool:
        """Return True if currently connected and device is available."""
        return bool(self._connected and self.device and getattr(self.device, "available", False))

    def shell(self, command: str) -> str:
        """Execute a shell command on the Shield, reconnecting once if disconnected.

        :param command: Shell command to run.
        :return: Command stdout string.
        """
        for attempt in range(2):
            try:
                if not self.is_connected():
                    self.connect()
                assert self.device is not None
                output = self.device.shell(command, timeout_s=self.timeout)
                return output if output is not None else ""
            except (ConnectionResetError, AdbConnectionError, AdbTimeoutError, BrokenPipeError, OSError) as exc:
                self.disconnect()
                if attempt == 0:
                    logger.debug("ADB connection dropped, retrying: %s", exc)
                    continue
                raise ShieldConnectionError(
                    f"Failed to execute command '{command}' on Shield ({self.host}:{self.port}): {exc}"
                ) from exc
        raise ShieldConnectionError(f"Shield is unreachable: command '{command}' failed.")

    def press(self, button: str) -> None:
        """Send a button press / keyevent to the Shield.

        :param button: Button name (e.g. 'home', 'back', 'up', 'down', 'enter', 'menu', 'mute').
        """
        key = button.strip().lower()
        if key not in self.buttons:
            raise ShieldButtonNotFoundError(
                f"Unknown button '{button}'. Valid buttons are: {', '.join(sorted(self.buttons.keys()))}"
            )
        keycode = self.buttons[key]
        self.shell(f"input keyevent {keycode}")

    def send_text(self, text: str) -> None:
        """Send text input to the Shield, properly escaping spaces and special characters.

        :param text: Text string to input.
        """
        escaped = escape_adb_text(text)
        if escaped:
            self.shell(f"input text {escaped}")

    def launch(self, app: str) -> None:
        """Launch an application on the Shield.

        If target is in format 'package/activity', am start is attempted first;
        if that fails or only a package name is given, monkey is used to launch
        the package's LEANBACK_LAUNCHER activity.

        :param app: App preset name (e.g. 'netflix', 'youtube', 'max') or package name.
        """
        app_key = app.strip().lower()
        if app_key in self.apps:
            target = self.apps[app_key]
        elif "." in app:
            target = app.strip()
        else:
            raise ShieldAppNotFoundError(
                f"No such app '{app}'. Valid apps are: {', '.join(sorted(self.apps.keys()))}"
            )

        # Check if target contains explicit activity (e.g. package/activity)
        if "/" in target:
            pkg, activity = target.split("/", 1)
            # Try am start first
            out = ""
            try:
                out = self.shell(f"am start -n {target}")
            except Exception as exc:
                logger.debug("am start -n %s failed: %s; trying monkey launcher fallback", target, exc)
                out = "Error"

            # Check if am start reported an error
            err_keywords = ("error", "does not exist", "not found", "securityexception")
            if any(k in out.lower() for k in err_keywords):
                logger.info("am start reported failure for %s, falling back to monkey launcher", target)
                self.shell(f"monkey -p {pkg} -c android.intent.category.LEANBACK_LAUNCHER 1")
        else:
            # Only package name provided: launch directly via monkey
            self.shell(f"monkey -p {target} -c android.intent.category.LEANBACK_LAUNCHER 1")

    def list_apps(self) -> list[str]:
        """Query installed Leanback packages on the Shield."""
        packages: set[str] = set()

        # Try querying leanback activities
        try:
            out = self.shell(
                "pm query-intent-activities -a android.intent.action.MAIN -c android.intent.category.LEANBACK_LAUNCHER"
            )
            for match in re.finditer(r"packageName=([a-zA-Z0-9._]+)", out or ""):
                packages.add(match.group(1))
        except Exception as exc:
            logger.debug("Query leanback activities failed: %s", exc)

        # Fallback to pm list packages if query returned empty
        if not packages:
            try:
                out = self.shell("pm list packages")
                for line in (out or "").splitlines():
                    line = line.strip()
                    if line.startswith("package:"):
                        packages.add(line[len("package:"):].strip())
            except Exception as exc:
                logger.debug("pm list packages failed: %s", exc)

        return sorted(packages)


class shield(Shield):
    """Backward-compatible alias for Shield class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "'shield' is deprecated and will be removed in a future release; use 'Shield' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
