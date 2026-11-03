"""Command-line interface for nvidia_shield_remote."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from nvidia_shield_remote.config import (
    load_config,
    resolve_shield_host,
    save_shield_host,
)
from nvidia_shield_remote.core import DEFAULT_APPS, DEFAULT_BUTTONS, Shield
from nvidia_shield_remote.exceptions import (
    ShieldAppNotFoundError,
    ShieldAuthError,
    ShieldButtonNotFoundError,
    ShieldConfigError,
    ShieldConnectionError,
    ShieldError,
)


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for shield-cli."""
    parser = argparse.ArgumentParser(
        prog="shield-cli",
        description="CLI tool to control Nvidia Shield TV over ADB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  shield-cli --list-commands
  shield-cli --save-ip 192.168.1.130:5555
  shield-cli -c home
  shield-cli -c down center
  shield-cli -c down -c center
  shield-cli -a netflix
  shield-cli -t "The Matrix"
  shield-cli --ip 192.168.1.130 -c volume up
""",
    )

    parser.add_argument(
        "-c",
        "--command",
        nargs="+",
        action="append",
        metavar="CMD",
        help="Send one or more button commands in sequence (e.g. -c home, or -c down center).",
    )
    parser.add_argument(
        "-a",
        "--app",
        metavar="APP",
        help="Launch an application preset or package (e.g. -a netflix, -a max, -a com.wbd.stream).",
    )
    parser.add_argument(
        "-t",
        "--text",
        metavar="TEXT",
        help="Send text input string to the Shield.",
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="List all recognized button commands and exit.",
    )
    parser.add_argument(
        "--list-apps",
        action="store_true",
        help="List available app presets and query installed Leanback apps from Shield.",
    )
    parser.add_argument(
        "--ip",
        "--host",
        dest="host",
        metavar="HOST[:PORT]",
        help="Specify the Shield TV IP/hostname and optional port (overrides config).",
    )
    parser.add_argument(
        "--save-ip",
        nargs="?",
        const=True,
        metavar="HOST[:PORT]",
        help="Save the Shield IP/host to config file (~/.config/nvidia-shield-remote/config.toml).",
    )

    return parser


def format_command_list() -> str:
    """Format available button commands for display."""
    lines = ["Available button commands:"]
    # Group and sort unique button names
    unique_keys = sorted(DEFAULT_BUTTONS.keys())
    for btn in unique_keys:
        keycode = DEFAULT_BUTTONS[btn]
        lines.append(f"  {btn:<14} -> {keycode}")
    return "\n".join(lines)


def format_apps_list(built_in_only: bool = True, installed: list[str] | None = None) -> str:
    """Format available apps for display."""
    lines = ["Configured app presets:"]
    for app_name in sorted(DEFAULT_APPS.keys()):
        target = DEFAULT_APPS[app_name]
        lines.append(f"  {app_name:<14} -> {target}")

    config_data = load_config()
    custom_apps = config_data.get("apps", {})
    if isinstance(custom_apps, dict) and custom_apps:
        lines.append("\nUser-defined app overrides:")
        for k, v in sorted(custom_apps.items()):
            lines.append(f"  {k:<14} -> {v}")

    if installed:
        lines.append("\nInstalled Leanback packages on Shield:")
        for pkg in sorted(installed):
            lines.append(f"  {pkg}")

    return "\n".join(lines)


def run_cli(args_list: Sequence[str] | None = None) -> int:
    """Parse arguments and execute CLI operations. Return exit code."""
    parser = create_parser()
    args = parser.parse_args(args_list)

    # 1. Handle non-connection informational options
    if args.list_commands:
        print(format_command_list())
        return 0

    # 2. Handle saving IP
    if args.save_ip is not None:
        ip_to_save: str | None = None
        if isinstance(args.save_ip, str):
            ip_to_save = args.save_ip.strip()
        elif args.host:
            ip_to_save = args.host.strip()

        if not ip_to_save:
            print("Error: No IP address specified to save. Use --save-ip <HOST[:PORT]>.", file=sys.stderr)
            return 2

        saved_path = save_shield_host(ip_to_save)
        print(f"Shield host successfully saved to {saved_path}: {ip_to_save}")
        if not (args.command or args.app or args.text or args.list_apps):
            return 0

    # Check if any action was requested
    has_action = bool(args.command or args.app or args.text or args.list_apps)
    if not has_action:
        parser.print_help(file=sys.stderr)
        return 2

    # 3. Resolve Shield host
    host = resolve_shield_host(args.host)
    if not host:
        print(
            "Error: Shield host/IP is not configured.\n"
            "Specify via --ip <HOST[:PORT]>, SHIELD_IP_PORT environment variable,\n"
            "or save it permanently with: shield-cli --save-ip <HOST[:PORT]>",
            file=sys.stderr,
        )
        return 2

    # 4. Handle --list-apps: try connecting to query, or fall back to local listing
    if args.list_apps and not (args.command or args.app or args.text):
        try:
            device = Shield(host=host, auto_connect=True)
            installed = device.list_apps()
            print(format_apps_list(installed=installed))
            return 0
        except (ShieldConnectionError, ShieldAuthError, OSError) as exc:
            print(f"Warning: Could not query installed apps from Shield ({exc}).", file=sys.stderr)
            print(format_apps_list())
            return 0

    # 5. Connect and execute remote commands
    try:
        device = Shield(host=host, auto_connect=True)
    except ShieldConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except ShieldAuthError as exc:
        print(f"Authentication error: {exc}", file=sys.stderr)
        return 1
    except ShieldConnectionError as exc:
        print(f"Connection error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected connection failure: {exc}", file=sys.stderr)
        return 1

    # Execute requested commands
    try:
        # Button commands
        if args.command:
            # Flatten list of lists from nargs='+', action='append'
            commands: list[str] = [cmd for group in args.command for cmd in group]
            for cmd in commands:
                device.press(cmd)
                print(f"Sent command: {cmd}")

        # Text input
        if args.text:
            device.send_text(args.text)
            print(f"Sent text: {args.text}")

        # Launch app
        if args.app:
            device.launch(args.app)
            print(f"Launched app: {args.app}")

        # List apps (if combined with other actions)
        if args.list_apps:
            installed = device.list_apps()
            print(format_apps_list(installed=installed))

        return 0

    except ShieldButtonNotFoundError as exc:
        print(f"Command error: {exc}", file=sys.stderr)
        return 2
    except ShieldAppNotFoundError as exc:
        print(f"App error: {exc}", file=sys.stderr)
        return 2
    except ShieldConnectionError as exc:
        print(f"Connection lost during command execution: {exc}", file=sys.stderr)
        return 1
    except ShieldError as exc:
        print(f"Error executing command: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 3


def main() -> None:
    """CLI entry point."""
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
