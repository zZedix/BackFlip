"""Interactive Backflip management CLI."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict

import questionary
import yaml

from .config import (
    DEFAULT_CONFIG_PATH,
    LOG_FILE,
    SYSTEMD_UNIT_PATH,
    ConfigurationError,
    load_config,
)

MENU_ACTIONS: Dict[str, Callable[[], None]] = {}
SERVICE_NAME = "backflip"
INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/zZedix/BackFlip/main/install.sh"
BANNER = "Backflip Service Manager\nCreated by zZedix — https://github.com/zZedix"


def menu_action(label: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def decorator(func: Callable[[], None]) -> Callable[[], None]:
        MENU_ACTIONS[label] = func
        return func

    return decorator


def require_systemctl() -> str:
    systemctl = shutil.which("systemctl")
    if not systemctl:
        raise RuntimeError("systemctl not found on PATH; systemd is required for Backflip")
    return systemctl


def require_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError("This action requires root privileges. Please re-run with sudo.")


def _run_command(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Command failed: {' '.join(command)} (exit code {exc.returncode})") from exc


def _tail_file(path: Path, lines: int = 50) -> None:
    if not path.exists():
        print(f"Log file {path} not found.")
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = handle.readlines()
    for line in data[-lines:]:
        print(line.rstrip())


def _show_logs() -> None:
    journalctl = shutil.which("journalctl")
    if journalctl:
        try:
            subprocess.run([journalctl, "-u", SERVICE_NAME, "-n", "50", "--no-pager"], check=False)
            return
        except Exception as exc:  # pragma: no cover - defensive
            print(f"journalctl failed: {exc}; falling back to log file")
    _tail_file(LOG_FILE)


def _restart_service() -> None:
    require_root()
    systemctl = require_systemctl()
    _run_command([systemctl, "restart", SERVICE_NAME])
    print("Service restarted.")


def _update_backflip() -> None:
    require_root()
    command = [
        "bash",
        "-lc",
        f"curl -fsSL {INSTALL_SCRIPT_URL} | bash",
    ]
    print("Fetching and running latest installer script...")
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as exc:
        print(f"Unable to launch update command: {exc}")
        return
    except subprocess.CalledProcessError as exc:
        print(f"Update script failed with exit code {exc.returncode}")
        return

    if questionary.confirm("Restart the Backflip service now?", default=True).ask():
        _restart_service()


def _show_settings() -> None:
    try:
        config = load_config()
    except ConfigurationError as exc:
        print(f"Error loading configuration: {exc}")
        return
    yaml_dump = yaml.safe_dump(config.to_dict(), sort_keys=False)
    print(yaml_dump)


def _edit_settings() -> None:
    require_root()
    editor = os.environ.get("EDITOR") or "nano"
    print(f"Opening {DEFAULT_CONFIG_PATH} with {editor}...")
    try:
        subprocess.run([editor, str(DEFAULT_CONFIG_PATH)], check=True)
    except FileNotFoundError as exc:
        print(f"Editor not found: {editor} ({exc})")
        return
    except subprocess.CalledProcessError as exc:
        print(f"Editor exited with {exc.returncode}; configuration not reloaded")
        return

    if questionary.confirm("Restart the Backflip service now?", default=True).ask():
        _restart_service()


def _uninstall() -> None:
    require_root()
    if not questionary.confirm("This will stop the tunnel and remove all Backflip files. Continue?", default=False).ask():
        print("Uninstall cancelled.")
        return

    systemctl = require_systemctl()
    subprocess.run([systemctl, "stop", SERVICE_NAME], check=False)
    subprocess.run([systemctl, "disable", SERVICE_NAME], check=False)
    if SYSTEMD_UNIT_PATH.exists():
        SYSTEMD_UNIT_PATH.unlink()
    if DEFAULT_CONFIG_PATH.exists():
        DEFAULT_CONFIG_PATH.unlink()
    subprocess.run([systemctl, "daemon-reload"], check=False)
    print("Backflip service uninstalled. You may remove the Python package if desired.")


@menu_action("View Logs")
def action_view_logs() -> None:
    _show_logs()


@menu_action("Restart Tunnel")
def action_restart() -> None:
    try:
        _restart_service()
    except Exception as exc:
        print(exc)


@menu_action("Show Settings")
def action_show_settings() -> None:
    _show_settings()


@menu_action("Edit Settings")
def action_edit_settings() -> None:
    try:
        _edit_settings()
    except Exception as exc:
        print(exc)


@menu_action("Update Backflip")
def action_update_backflip() -> None:
    try:
        _update_backflip()
    except Exception as exc:
        print(exc)


@menu_action("Project GitHub Page")
def action_show_github() -> None:
    print("Repository: https://github.com/zZedix/BackFlip")


@menu_action("Uninstall")
def action_uninstall() -> None:
    try:
        _uninstall()
    except Exception as exc:
        print(exc)


def main() -> None:
    try:
        print(BANNER)
        while True:
            choices = list(MENU_ACTIONS.keys()) + ["Quit"]
            choice = questionary.select("Select an action", choices=choices).ask()
            if choice in (None, "Quit"):
                break
            action = MENU_ACTIONS.get(choice)
            if action:
                action()
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":  # pragma: no cover
    main()
